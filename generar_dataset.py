"""
Este script permite generar un dataset de contadores de agua
de la provincia de Alicante con:
    - ID_CONTADOR: identificador unico del contador (CNT_000001, CNT_000002, ...)
    - ID_CLIENTE: identificador unico del cliente (CLI_000001, CLI_000002, ...)
    - FECHA_BUILD: fecha de fabricacion del contador (entre 2015 y 2024)
    - FECHA_INSTALACION: fecha de instalacion del contador (entre 30 y 720 dias despues de la fabricacion, con limite maximo en la fecha de hoy para evitar fechas futuras)
    - LATITUD: latitud geografica del contador (dentro de los limites de la provincia de Alicante)
    - LONGITUD: longitud geografica del contador (dentro de los limites de la provincia de Alicante)
    - MUNICIPIO: municipio de Alicante al que pertenece el contador (Alicante, Elche, Torrevieja, Orihuela, Benidorm, Alcoy, San Vicente del Raspeig, Elda, Denia, Petrer, Villena, Sant Joan d'Alacant)

El dataset se guarda en formato CSV con el nombre "contadores_alicante.csv".

"""

import numpy as np
import pandas as pd
from datetime import date, timedelta

SEED = 42
np.random.seed(SEED)

NUM_CONTADORES = 5000

FECHA = date(2026, 5, 25)


# Diccionario de las ciudades de Alicante indicando latitud, longitud, poblacion y desviacion estandar de la gaussiana para generar coordenadas.
# Se indica la desiacion estandar de la gaussiana para cada ciudad, que se usara para
# generar coordenadas geograficas de los contadores, con el fin de que los contadores se agrupen alrededor de las ciudades y no se distribuyan uniformemente por toda la provincia.
CIUDADES = {
    "Alicante": (38.3452, -0.4810, 338000, 0.025),
    "Elche": (38.2655, -0.6983, 234000, 0.022),
    "Torrevieja": (37.9787, -0.6822, 83000, 0.018),
    "Orihuela": (38.0848, -0.9445, 78000, 0.020),
    "Benidorm": (38.5342, -0.1313, 70000, 0.012),
    "Alcoy": (38.6984, -0.4734, 59000, 0.012),
    "San Vicente del Raspeig": (38.3963, -0.5253, 58000, 0.012),
    "Elda": (38.4787, -0.7918, 52000, 0.012),
    "Denia": (38.8407, 0.1057, 42000, 0.015),
    "Petrer": (38.4839, -0.7700, 35000, 0.010),
    "Villena": (38.6370, -0.8662, 34000, 0.012),
    "Sant Joan d'Alacant": (38.4014, -0.4385, 24000, 0.009),
}

# Limites geograficos de la provincia de Alicante. Asi los contadores generados
# no se salen de la provincia.
LATITUD_MIN, LATITUD_MAX = 37.85, 38.93
LONGITUD_MIN, LONGITUD_MAX = -1.03, 0.23


def generar_coordenadas(n):
    """
    Metodo para generar coordenadas geograficas de contadores de agua en Alicante.
    Se asigna a cada contador una ciudad de Alicante con probabilidad proporcional a su poblacion.
    Luego se generan latitud y longitud a partir de la desviacion estandar de la gaussiana asignada a esa ciudad.

    Args:
    - n: numero de contadores a generar.
    """
    nombres = list(CIUDADES.keys())
    datos = np.array([CIUDADES[c][:4] for c in nombres])
    latitud, longitud, poblacion, sigmas_c = (
        datos[:, 0],
        datos[:, 1],
        datos[:, 2],
        datos[:, 3],
    )

    pesos = poblacion / poblacion.sum()
    idx = np.random.choice(len(nombres), size=n, p=pesos)  # ciudad de cada contador

    # Centro y dispersion que le toca a cada contador segun su ciudad.
    mu_lat, mu_lon, sigma = latitud[idx], longitud[idx], sigmas_c[idx]

    latitud = np.random.normal(mu_lat, sigma)
    longitud = np.random.normal(mu_lon, sigma)

    # Regulamos la latitud y longitud con las fronteras de la provincia para evitar valores
    # fuera de la provincia de Alicante.
    latitud = np.clip(latitud, LATITUD_MIN, LATITUD_MAX)
    longitud = np.clip(longitud, LONGITUD_MIN, LONGITUD_MAX)

    municipios = np.array(nombres)[idx]
    return latitud, longitud, municipios


def generar_fechas(n):
    """
    Metodo para generar las fechas de fabricacion e instalacion de los contadores.
    Se generarán entre 2015 y 2024 para la fabricacion, y la instalacion se generara entre 30 y 720 dias despues de la fabricacion,
    con un limite maximo en la fecha de hoy (2026-05-25) para evitar fechas futuras.

    Args:
        - n: numero de contadores a generar.
    """

    # Formamos los rangos de fechas para cada etapa del ciclo de vida del contador.
    hoy = FECHA
    fecha_inicio_fabricacion = date(2015, 1, 1)
    fecha_fin_fabricacion = date(2024, 12, 31)
    dias_rango_fabricacion = (fecha_fin_fabricacion - fecha_inicio_fabricacion).days

    # Generacion de fechas de fabricacion
    rango_dias_fabricacion = np.random.randint(0, dias_rango_fabricacion + 1, size=n)
    fechas_fabricacion = [
        fecha_inicio_fabricacion + timedelta(days=int(d))
        for d in rango_dias_fabricacion
    ]

    # Generacion de fechas de instalacion entre 30 y 720 dias
    dias_espera_instalacion = np.random.randint(30, 721, size=n)
    fechas_instalacion = []
    for fecha_fabricacion, dias in zip(fechas_fabricacion, dias_espera_instalacion):
        fecha_instalacion = fecha_fabricacion + timedelta(days=int(dias))
        if fecha_instalacion > hoy:
            fecha_instalacion = hoy
        fechas_instalacion.append(fecha_instalacion)

    return fechas_fabricacion, fechas_instalacion


def main():
    lat, lon, municipios = generar_coordenadas(NUM_CONTADORES)
    fechas_build, fechas_inst = generar_fechas(NUM_CONTADORES)

    df = pd.DataFrame(
        {
            "ID_CONTADOR": [f"CNT_{i:06d}" for i in range(1, NUM_CONTADORES + 1)],
            "ID_CLIENTE": [f"CLI_{i:06d}" for i in range(1, NUM_CONTADORES + 1)],
            "FECHA_BUILD": fechas_build,
            "FECHA_INSTALACION": fechas_inst,
            "LATITUD": np.round(lat, 6),
            "LONGITUD": np.round(lon, 6),
            "MUNICIPIO": municipios,  # auxiliar: permite verificar el cluster
        }
    )

    salida = "contadores_alicante.csv"
    df.to_csv(salida, index=False)

    # --- Resumen de verificacion ---
    print(f"Dataset generado: {salida}  ({len(df)} contadores)")
    print(f"Latitud  : {df['LATITUD'].min():.4f} .. {df['LATITUD'].max():.4f}")
    print(f"Longitud : {df['LONGITUD'].min():.4f} .. {df['LONGITUD'].max():.4f}")
    ok_orden = (df["FECHA_BUILD"] < df["FECHA_INSTALACION"]).all()
    print(f"build < instalacion en todas las filas: {ok_orden}")
    print("\nContadores por municipio:")
    print(df["MUNICIPIO"].value_counts().to_string())
    print("\nPrimeras filas:")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
