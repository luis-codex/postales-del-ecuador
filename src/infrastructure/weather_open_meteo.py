"""Real weather for the place, right now. Open-Meteo, no API key.

WMO codes are Open-Meteo protocol, not domain vocabulary: that is why the table
lives here and what leaves this module is already a Weather.
"""

import json
import urllib.request

from domain.models import Place, Weather

WMO_CODES = {
    0: "cielo despejado", 1: "mayormente despejado", 2: "parcialmente nublado", 3: "cubierto",
    45: "niebla", 48: "niebla con escarcha", 51: "llovizna ligera", 53: "llovizna",
    55: "llovizna densa", 56: "llovizna helada", 57: "llovizna helada densa",
    61: "lluvia ligera", 63: "lluvia", 65: "lluvia fuerte", 66: "lluvia helada",
    67: "lluvia helada fuerte", 71: "nevada ligera", 73: "nevada", 75: "nevada fuerte",
    77: "granos de nieve", 80: "chubascos ligeros", 81: "chubascos", 82: "chubascos violentos",
    85: "chubascos de nieve", 86: "chubascos de nieve fuertes",
    95: "tormenta electrica", 96: "tormenta con granizo", 99: "tormenta con granizo fuerte",
}


class OpenMeteoWeather:
    def __init__(self, timeout=12):
        self._timeout = timeout

    def fetch(self, place: Place) -> Weather:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={place.lat}&longitude={place.lon}"
            "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,is_day"
            "&timezone=America%2FGuayaquil"
        )
        request = urllib.request.Request(
            url, headers={"User-Agent": "postales-del-ecuador/1.0"})
        with urllib.request.urlopen(request, timeout=self._timeout) as response:
            current = json.loads(response.read().decode())["current"]

        code = int(current.get("weather_code", 0))
        return Weather(
            temperature=round(float(current.get("temperature_2m", 0)), 1),
            humidity=int(current.get("relative_humidity_2m", 0)),
            wind=round(float(current.get("wind_speed_10m", 0)), 1),
            description=WMO_CODES.get(code, "cielo variable"),
            code=code,
            is_daytime=bool(current.get("is_day", 1)),
        )
