"""Clima real del lugar, ahora mismo. Open-Meteo, sin clave de API.

Los codigos WMO son protocolo de Open-Meteo, no vocabulario del dominio: por eso
la tabla vive aqui y lo que sale de este modulo ya es un Clima.
"""

import json
import urllib.request

from dominio.modelos import Clima, Lugar

CODIGOS_WMO = {
    0: "cielo despejado", 1: "mayormente despejado", 2: "parcialmente nublado", 3: "cubierto",
    45: "niebla", 48: "niebla con escarcha", 51: "llovizna ligera", 53: "llovizna",
    55: "llovizna densa", 56: "llovizna helada", 57: "llovizna helada densa",
    61: "lluvia ligera", 63: "lluvia", 65: "lluvia fuerte", 66: "lluvia helada",
    67: "lluvia helada fuerte", 71: "nevada ligera", 73: "nevada", 75: "nevada fuerte",
    77: "granos de nieve", 80: "chubascos ligeros", 81: "chubascos", 82: "chubascos violentos",
    85: "chubascos de nieve", 86: "chubascos de nieve fuertes",
    95: "tormenta electrica", 96: "tormenta con granizo", 99: "tormenta con granizo fuerte",
}


class ClimaOpenMeteo:
    def __init__(self, tiempo_espera=12):
        self._tiempo_espera = tiempo_espera

    def consultar(self, lugar: Lugar) -> Clima:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lugar.lat}&longitude={lugar.lon}"
            "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,is_day"
            "&timezone=America%2FGuayaquil"
        )
        peticion = urllib.request.Request(
            url, headers={"User-Agent": "postales-del-ecuador/1.0"})
        with urllib.request.urlopen(peticion, timeout=self._tiempo_espera) as respuesta:
            actual = json.loads(respuesta.read().decode())["current"]

        codigo = int(actual.get("weather_code", 0))
        return Clima(
            temperatura=round(float(actual.get("temperature_2m", 0)), 1),
            humedad=int(actual.get("relative_humidity_2m", 0)),
            viento=round(float(actual.get("wind_speed_10m", 0)), 1),
            descripcion=CODIGOS_WMO.get(codigo, "cielo variable"),
            codigo=codigo,
            es_de_dia=bool(actual.get("is_day", 1)),
        )
