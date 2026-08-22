"""Que escribir hoy, decidido a partir de lo que ya se escribio.

Esta es la diferencia entre un agente y un cron con una clave de API: antes de
escribir, mira su memoria y elige deliberadamente algo que no ha hecho. Sin esta
capa, treinta dias de postales serian la misma postal treinta veces.

El catalogo llega como parametro: de donde salen los lugares no es asunto del
dominio.
"""

import random

from .modelos import Lugar

TONOS = [
    "melancolico y contenido",
    "luminoso y agradecido",
    "seco y observacional, casi periodistico",
    "nostalgico de algo que no se nombra",
    "asombrado, como quien llega por primera vez",
    "intimo, dirigido a una segunda persona",
    "sobrio y geologico, atento al tiempo largo",
    "humoristico sin dejar de ser tierno",
    "inquieto, con algo de presagio",
    "sensorial y concreto, puro olor y textura",
    "reflexivo sobre el paso del tiempo",
    "callado, como una nota dejada sobre la mesa",
]

LUGARES_QUE_RECUERDA = 18
TONOS_QUE_RECUERDA = 8


def elegir_lugar(memoria, catalogo) -> Lugar:
    recientes = {postal.lugar for postal in memoria[:LUGARES_QUE_RECUERDA]}
    disponibles = [lugar for lugar in catalogo if lugar.nombre not in recientes]
    return random.choice(disponibles or catalogo)


def elegir_tono(memoria) -> str:
    usados = {postal.tono for postal in memoria[:TONOS_QUE_RECUERDA]}
    disponibles = [tono for tono in TONOS if tono not in usados]
    return random.choice(disponibles or TONOS)
