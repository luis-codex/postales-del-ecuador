"""Carga el catalogo de lugares desde data/.

Los cincuenta lugares son datos, no reglas: viven en un JSON aparte y este
adaptador los convierte en modelos del dominio. Asi el dominio recibe el
catalogo inyectado en vez de importarlo, y sigue sin depender de nada.
"""

import json
from pathlib import Path

from dominio.modelos import Lugar

RUTA = Path(__file__).resolve().parent.parent / "data" / "lugares.json"


def cargar(ruta=RUTA):
    with open(ruta, encoding="utf-8") as archivo:
        return [Lugar(**registro) for registro in json.load(archivo)]
