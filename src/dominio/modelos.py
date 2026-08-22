"""Los tipos del dominio.

Ningun adaptador impone su forma aqui: DynamoDB, Open-Meteo y Bedrock traducen
a estos modelos en la frontera, y el dominio no sabe que existen.
"""

from dataclasses import dataclass
from datetime import timezone, timedelta

ZONA_ECUADOR = timezone(timedelta(hours=-5))


@dataclass(frozen=True)
class Lugar:
    nombre: str
    provincia: str
    lat: float
    lon: float
    alma: str


@dataclass(frozen=True)
class Clima:
    temperatura: float
    humedad: int
    viento: float
    descripcion: str
    codigo: int
    es_de_dia: bool


@dataclass(frozen=True)
class Borrador:
    titulo: str
    texto: str


@dataclass(frozen=True)
class Postal:
    id: str
    epoch: int
    lugar: str
    provincia: str
    titulo: str
    texto: str
    tono: str
    clima: Clima
    generada_en: str
    disparador: str
    modelo: str
