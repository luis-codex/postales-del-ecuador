"""Translates the weather into how the body feels.

This is the piece that decides how good the postcards are. The model is never
shown a number, so it cannot recite one: all it can write about is what being
there feels like. Before this, postcards said "the temperature is 25.4 degrees
which feel cooler because of the humidity, 66%".
"""

from .models import Weather


def _on_the_body(temperature: float) -> str:
    if temperature < 0:
        return "frio que corta la cara y entumece los dedos"
    if temperature < 8:
        return "frio de paramo, de meter las manos en los bolsillos"
    if temperature < 14:
        return "fresco, se agradece una chompa"
    if temperature < 19:
        return "templado, ni frio ni calor"
    if temperature < 24:
        return "tibio, comodo en manga corta"
    if temperature < 29:
        return "calor, la sombra se vuelve importante"
    return "calor pesado, de buscar donde sentarse quieto"


def _the_air(humidity: int) -> str:
    if humidity >= 85:
        return "aire saturado, todo lo que se toca esta un poco mojado"
    if humidity >= 70:
        return "aire humedo, la ropa tarda en secarse"
    if humidity >= 50:
        return "aire normal"
    return "aire seco, los labios se parten"


def _the_wind(wind: float) -> str:
    if wind < 5:
        return "sin viento, el aire quieto"
    if wind < 15:
        return "brisa suave"
    if wind < 30:
        return "viento constante que no para"
    return "viento fuerte, cuesta caminar derecho"


def _what_the_combination_adds(temperature: float, humidity: int) -> str:
    if temperature >= 24 and humidity >= 70:
        return " Se suda sin moverse."
    if temperature < 8 and humidity >= 80:
        return " El frio es humedo, entra hasta los huesos."
    return ""


def describe(weather: Weather) -> str:
    return (
        f"- En el cuerpo: {_on_the_body(weather.temperature)}\n"
        f"- El aire: {_the_air(weather.humidity)}\n"
        f"- El viento: {_the_wind(weather.wind)}\n"
        f"- El cielo: {weather.description}."
        f"{_what_the_combination_adds(weather.temperature, weather.humidity)}"
    )


def time_of_day(now, is_daytime: bool) -> str:
    if not is_daytime:
        return "de noche"
    if now.hour < 7:
        return "al amanecer"
    if now.hour < 12:
        return "por la manana"
    if now.hour < 15:
        return "al mediodia"
    if now.hour < 19:
        return "por la tarde"
    return "al anochecer"
