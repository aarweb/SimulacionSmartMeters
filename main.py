import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random


class ContadorAguaVisual:
    def __init__(self, contador_id):
        self.contador_id = contador_id

        # Parámetros de los 3 picos: [Peso (w), Media (mu), Desviación (sigma)]
        self.picos = [[0.4, 8.0, 1.0], [0.2, 14.5, 1.2], [0.4, 21.0, 1.5]]

        self.offset_individual = random.uniform(-0.75, 0.75)

        self.probabilidad_base = 0.002

        self.intensidad_base = random.uniform(0.6, 1.4)

    def calcular_probabilidad(self, hora):
        """
        Calcula la densidad de probabilidad para una hora especifica del dia (0-24)
        """
        hora_ajustada = (hora + self.offset_individual) % 24

        prob_picos = 0
        for w, mu, sigma in self.picos:
            # Ecuación de la distribución normal (Gaussiana)

            exponente = -0.5 * ((hora_ajustada - mu) / sigma) ** 2
            gaussiana = 1 / (sigma * np.sqrt(2 * np.pi)) * np.exp(exponente)
            prob_picos += w * gaussiana

        return (prob_picos * self.intensidad_base) + self.probabilidad_base

    def simular_dia(self, intervalo_minutos=1):
        """
        Simula un dia completo minuto a minuto y retorna las horas de los pulsos generados
        """
        pulsos_detectados = []
        pasos_totales = int(24 * (60 / intervalo_minutos))
        horas_dia = np.linspace(0, 24, pasos_totales)

        ticks_por_hora = 60 / intervalo_minutos

        for hora in horas_dia:
            prob_hora = self.calcular_probabilidad(hora)

            # Escalamos la probabilidad horaria al tamaño del tick temporal.
            prob_tick = prob_hora / ticks_por_hora

            # Proceso de Bernoulli (Lanzamiento de moneda sesgada)
            if random.random() < prob_tick:
                pulsos_detectados.append(hora)

        return pulsos_detectados


# ==========================================
# CONFIGURACIÓN Y EJECUCIÓN DE LA SIMULACIÓN
# ==========================================

sns.set_theme(style="whitegrid")
plt.rcParams.update({"font.size": 11, "figure.titlesize": 16})

num_contadores = 30
contadores = [
    ContadorAguaVisual(f"Contador-{i + 1:02d}") for i in range(num_contadores)
]

todos_los_pulsos = {}
lista_global_de_pulsos = []

for c in contadores:
    pulsos = c.simular_dia(intervalo_minutos=1)  # Simulación minuto a minuto
    todos_los_pulsos[c.contador_id] = pulsos
    lista_global_de_pulsos.extend(pulsos)

# ==========================================
# GENERACIÓN DE GRÁFICOS (3 PANELES)
# ==========================================

fig, axes = plt.subplots(
    3, 1, figsize=(12, 12), sharex=True, gridspec_kw={"height_ratios": [1.5, 3, 2]}
)

# --- PANEL 1: Curva Teórica de Probabilidad ---
eje_x_horas = np.linspace(0, 24, 500)
contador_teorico = ContadorAguaVisual("Teórico")
contador_teorico.offset_individual = 0  # Sin desfase para ver patrón limpio
contador_teorico.intensidad_base = 1.0
y_teorico = [contador_teorico.calcular_probabilidad(h) for h in eje_x_horas]

axes[0].plot(
    eje_x_horas,
    y_teorico,
    color="#1f77b4",
    lw=2.5,
    label="Mezcla de 3 Gaussianas (GMM)",
)

axes[0].fill_between(eje_x_horas, y_teorico, alpha=0.15, color="#1f77b4")
axes[0].set_title(
    "Perfil de Probabilidad Teórica de Consumo Diario (GMM)",
    loc="left",
    fontweight="bold",
)
axes[0].set_ylabel("Densidad Prob.")
axes[0].legend()

# --- PANEL 2: Raster Plot (Pulsos individales desincronizados) ---
for idx, (cid, pulsos) in enumerate(todos_los_pulsos.items()):
    axes[1].scatter(
        pulsos, [idx] * len(pulsos), color="#e74c3c", alpha=0.6, s=15, marker="|"
    )


axes[1].set_title(
    "2. Registro de Pulsos Individuales (Simulación de 30 Contadores)",
    loc="left",
    fontweight="bold",
)
axes[1].set_ylabel("ID del Contador")
axes[1].set_yticks(range(num_contadores))
axes[1].set_yticklabels([f"C-{i + 1:02d}" for i in range(num_contadores)], fontsize=8)
axes[1].set_ylim(-1, num_contadores)

# --- PANEL 3: Histograma Acumulado (La Realidad Reconstruida) ---
sns.histplot(
    lista_global_de_pulsos,
    bins=48,
    kde=True,
    ax=axes[2],
    color="#2ecc71",
    edgecolor="white",
    alpha=0.7,
)
axes[2].set_title(
    "3. Volumen de Consumo Agregado Registrado (Suma de todos los pulsos)",
    loc="left",
    fontweight="bold",
)
axes[2].set_xlabel("Hora del día (00:00 - 24:00)")
axes[2].set_ylabel("Pulsos Emitidos (Listros)")
axes[2].set_xlim(0, 24)
axes[2].set_xticks(range(25))
plt.tight_layout()
plt.show()
