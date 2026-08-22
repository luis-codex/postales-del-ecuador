"""Las reglas que una postal tiene que cumplir para publicarse.

Nadie mira lo que escribe el agente a las seis de la manana, asi que el agente
se corrige solo: si el borrador incumple alguna regla, se descarta y se vuelve
a pedir.
"""

import re

from .modelos import Borrador, Lugar

PALABRAS_PROHIBIDAS = [
    "magic", "encant", "paraiso", "paraíso", "joya", "imperdible", "mistic", "místic",
    "maravillos", "hermos", "destino turistico", "destino turístico", "inolvidable",
]

MINIMO_PALABRAS = 85
MAXIMO_PALABRAS = 145
MAXIMO_PALABRAS_TITULO = 7


def revisar(borrador: Borrador, lugar: Lugar, tono: str) -> list:
    texto = (borrador.texto or "").strip()
    titulo = (borrador.titulo or "").strip()

    if not texto:
        return ["postal vacia"]

    fallos = []

    palabras = len(texto.split())
    if not MINIMO_PALABRAS <= palabras <= MAXIMO_PALABRAS:
        fallos.append(f"longitud {palabras}")

    if re.search(r"\d", texto):
        fallos.append("contiene numeros")

    encontradas = [p for p in PALABRAS_PROHIBIDAS if p in texto.lower()]
    if encontradas:
        fallos.append(f"palabras prohibidas {encontradas}")

    if not titulo:
        fallos.append("titulo vacio")
        return fallos

    en_minusculas = titulo.lower()
    if (lugar.nombre.split(",")[0].lower() in en_minusculas
            or lugar.provincia.lower() in en_minusculas):
        fallos.append("el titulo nombra el lugar")

    if len(titulo.split()) > MAXIMO_PALABRAS_TITULO:
        fallos.append("titulo demasiado largo")

    delatoras = [p for p in re.findall(r"\w{5,}", tono.lower()) if p in en_minusculas]
    if delatoras:
        fallos.append(f"el titulo copia el tono {delatoras}")

    return fallos
