import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import random


# ==========================================================================
# PERFILES DE COMPORTAMIENTO (configurables)
# --------------------------------------------------------------------------
# Cada perfil define el "tipo de hogar" detrás de un contador. Para cambiar
# el comportamiento de los usuarios basta con editar este diccionario o añadir
# un perfil nuevo: no hay que tocar la lógica de simulación.
#
# Campos de cada perfil:
#   - picos:      lista de [peso (w), hora central (mu), desviación (sigma)]
#                 que define el Modelo de Mezcla de Gaussianas (GMM).
#   - intensidad: rango (min, max) del multiplicador I_familiar. Simula
#                 hogares con mucho o poco consumo.
#   - fuga:       opciones de fuga residual (L/h). Se elige una al azar; el
#                 0.0 representa "sin fuga". Repetir 0.0 baja la probabilidad.
#   - offset:     rango (min, max) en horas del desfase horario individual,
#                 para desincronizar los hábitos de cada hogar.
# ==========================================================================
PERFILES = {
    # Hogar "tipo": los 3 picos clásicos (mañana, mediodía, noche).
    "estandar": {
        "picos": [[0.4, 8.0, 1.0], [0.2, 14.5, 1.2], [0.4, 21.0, 1.5]],
        "intensidad": (0.8, 1.2),
        "fuga": [0.0, 0.0, 0.0, 0.05],  # 25% de probabilidad de fuga
        "offset": (-0.75, 0.75),
    },
    # Familia numerosa: mucho consumo y mañanas largas (varias duchas).
    "familia_numerosa": {
        "picos": [[0.45, 8.0, 1.4], [0.2, 14.5, 1.2], [0.35, 21.0, 1.6]],
        "intensidad": (1.6, 2.6),
        "fuga": [0.0, 0.0, 0.05],
        "offset": (-0.5, 0.5),
    },
    # Persona sola: poco consumo, ducha rápida, cena tardía.
    "persona_sola": {
        "picos": [[0.5, 8.5, 0.6], [0.1, 14.0, 1.0], [0.4, 22.0, 1.0]],
        "intensidad": (0.3, 0.6),
        "fuga": [0.0, 0.0, 0.0, 0.0],  # vive fuera muchas horas: rara vez fuga
        "offset": (-1.0, 1.0),
    },
    # Trabajador nocturno: hábitos invertidos, consume de madrugada y duerme
    # por la mañana. En la franja 07:00-09:00 apenas genera pulsos.
    "trabajador_nocturno": {
        "picos": [[0.4, 2.0, 1.5], [0.3, 13.0, 1.0], [0.3, 18.0, 1.0]],
        "intensidad": (0.7, 1.3),
        "fuga": [0.0, 0.0, 0.05],
        "offset": (-0.75, 0.75),
    },
    # Casa con fuga: consumo normal pero SIEMPRE pierde agua (caso a detectar).
    "casa_con_fuga": {
        "picos": [[0.4, 8.0, 1.0], [0.2, 14.5, 1.2], [0.4, 21.0, 1.5]],
        "intensidad": (0.6, 1.0),
        "fuga": [0.05, 0.08, 0.12],  # nunca 0.0: la fuga es constante
        "offset": (-0.75, 0.75),
    },
}

# Reparto de perfiles en la población simulada. Los pesos no necesitan sumar 1;
# random.choices los normaliza. Editar aquí cambia la composición de la ciudad.
DISTRIBUCION_PERFILES = {
    "estandar": 0.45,
    "familia_numerosa": 0.20,
    "persona_sola": 0.20,
    "trabajador_nocturno": 0.10,
    "casa_con_fuga": 0.05,
}


class ContadorIoT:
    def __init__(self, id_contador, perfil):
        self.id_contador = id_contador
        self.perfil = perfil
        # El comportamiento se deriva del perfil asignado a este contador.
        self.picos = perfil["picos"]
        self.offset = random.uniform(*perfil["offset"])
        self.intensidad = random.uniform(*perfil["intensidad"])
        self.fuga = random.choice(perfil["fuga"])

    def simular_bloque_horas(self, hora_inicio, hora_fin, ticks_por_segundo=1):
        """
        Simula un tramo de tiempo y retorna los pulsos generados en formato IoT
        """
        eventos = []

        # Simulación de un bloque temporal discreto
        for t in np.arange(hora_inicio, hora_fin, 1 / (3600 * ticks_por_segundo)):
            hora_ajustada = (t + self.offset) % 24

            # Evaluación del GMM con los picos propios del perfil
            prob_gmm = 0
            for w, mu, sigma in self.picos:
                exponente = -0.5 * ((hora_ajustada - mu) / sigma) ** 2
                prob_gmm += w * (1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(exponente)

            prob_final = (prob_gmm * self.intensidad) / (3600 * ticks_por_segundo)

            # Sumamos la probabilidad de fuga (si la hay) por cada segundo
            prob_final += self.fuga / (3600 * ticks_por_segundo)

            if random.random() < prob_final:
                eventos.append(
                    {
                        "timestamp": round(t, 4),
                        "sensor_id": self.id_contador,
                        "evento": "PULSO_1L",
                    }
                )

        return eventos


# Función de ejecución global que será mapeada a los procesos
def ejecutar_simulacion_contador(args):
    # Cada tarea recibe el id del contador y el nombre del perfil asignado.
    id_num, nombre_perfil = args
    # Simula el consumo de un contador entre las 07:00 y las 09:00 AM
    # (franja crítica de la mañana).
    contador = ContadorIoT(f"CNT_{id_num:06d}", PERFILES[nombre_perfil])
    eventos = contador.simular_bloque_horas(7.0, 9.0, ticks_por_segundo=1)
    return nombre_perfil, len(eventos)


if __name__ == "__main__":
    num_sensores = 5000  # Cantidad masiva de contadores a simular en paralelo
    print(
        f"Iniciando simulación paralela para {num_sensores} contadores inteligentes..."
    )

    # Asignamos dinámicamente un perfil a cada contador según la distribución.
    nombres_perfiles = list(DISTRIBUCION_PERFILES.keys())
    pesos_perfiles = list(DISTRIBUCION_PERFILES.values())
    asignaciones = random.choices(
        nombres_perfiles, weights=pesos_perfiles, k=num_sensores
    )

    inicio = time.time()
    with ProcessPoolExecutor() as executor:
        # Mapeamos (id, perfil) a la función simuladora distribuyéndolos en paralelo
        resultados = executor.map(
            ejecutar_simulacion_contador, zip(range(num_sensores), asignaciones)
        )

        # Procesar resultados agregados, desglosados por perfil de comportamiento
        pulsos_por_perfil = defaultdict(int)
        contadores_por_perfil = defaultdict(int)
        for nombre_perfil, n_pulsos in resultados:
            pulsos_por_perfil[nombre_perfil] += n_pulsos
            contadores_por_perfil[nombre_perfil] += 1

    fin_tiempo = time.time()

    total_pulsos_generados = sum(pulsos_por_perfil.values())
    tiempo_empleado = fin_tiempo - inicio

    print("\n--- RESULTADOS DE LA SIMULACIÓN CONCURRENTE ---")
    print(f"Tiempo total de cómputo: {tiempo_empleado:.2f} segundos")
    print(f"Pulsos de agua totales procesados: {total_pulsos_generados} eventos")
    print(
        f"Rendimiento de simulación: "
        f"{int(total_pulsos_generados / tiempo_empleado)} eventos/segundo"
    )

    print("\n--- DESGLOSE POR PERFIL DE COMPORTAMIENTO (07:00-09:00) ---")
    for nombre in nombres_perfiles:
        n_cont = contadores_por_perfil[nombre]
        n_pulsos = pulsos_por_perfil[nombre]
        media = n_pulsos / n_cont if n_cont else 0
        print(
            f"  {nombre:<20} | contadores: {n_cont:>5} | "
            f"pulsos: {n_pulsos:>7} | media: {media:>6.1f} pulsos/contador"
        )
