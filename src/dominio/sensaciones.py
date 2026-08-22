"""Traduce el clima a como se siente el cuerpo.

Es la pieza que decide la calidad de las postales. Al modelo nunca se le muestra
un numero, asi que no puede recitarlo: solo puede escribir sobre como se siente
estar ahi. Antes de esto las postales decian "la temperatura es de 25.4 grados
que se sienten mas frescos por la humedad, un 66%".
"""

from .modelos import Clima


def _en_el_cuerpo(temperatura):
    if temperatura < 0:
        return "frio que corta la cara y entumece los dedos"
    if temperatura < 8:
        return "frio de paramo, de meter las manos en los bolsillos"
    if temperatura < 14:
        return "fresco, se agradece una chompa"
    if temperatura < 19:
        return "templado, ni frio ni calor"
    if temperatura < 24:
        return "tibio, comodo en manga corta"
    if temperatura < 29:
        return "calor, la sombra se vuelve importante"
    return "calor pesado, de buscar donde sentarse quieto"


def _el_aire(humedad):
    if humedad >= 85:
        return "aire saturado, todo lo que se toca esta un poco mojado"
    if humedad >= 70:
        return "aire humedo, la ropa tarda en secarse"
    if humedad >= 50:
        return "aire normal"
    return "aire seco, los labios se parten"


def _el_viento(viento):
    if viento < 5:
        return "sin viento, el aire quieto"
    if viento < 15:
        return "brisa suave"
    if viento < 30:
        return "viento constante que no para"
    return "viento fuerte, cuesta caminar derecho"


def _lo_que_se_nota_al_juntarlo(temperatura, humedad):
    if temperatura >= 24 and humedad >= 70:
        return " Se suda sin moverse."
    if temperatura < 8 and humedad >= 80:
        return " El frio es humedo, entra hasta los huesos."
    return ""


def describir(clima: Clima) -> str:
    return (
        f"- En el cuerpo: {_en_el_cuerpo(clima.temperatura)}\n"
        f"- El aire: {_el_aire(clima.humedad)}\n"
        f"- El viento: {_el_viento(clima.viento)}\n"
        f"- El cielo: {clima.descripcion}."
        f"{_lo_que_se_nota_al_juntarlo(clima.temperatura, clima.humedad)}"
    )


def momento_del_dia(ahora, es_de_dia: bool) -> str:
    if not es_de_dia:
        return "de noche"
    if ahora.hour < 7:
        return "al amanecer"
    if ahora.hour < 12:
        return "por la manana"
    if ahora.hour < 15:
        return "al mediodia"
    if ahora.hour < 19:
        return "por la tarde"
    return "al anochecer"
