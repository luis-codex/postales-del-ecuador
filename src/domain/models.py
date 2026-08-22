"""The domain types.

No adapter imposes its shape here: DynamoDB, Open-Meteo and Bedrock translate
into these models at the boundary, and the domain does not know they exist.
"""

from dataclasses import dataclass
from datetime import timedelta, timezone

ECUADOR_TZ = timezone(timedelta(hours=-5))


@dataclass(frozen=True)
class Place:
    name: str
    province: str
    lat: float
    lon: float
    soul: str


@dataclass(frozen=True)
class Weather:
    temperature: float
    humidity: int
    wind: float
    description: str
    code: int
    is_daytime: bool


@dataclass(frozen=True)
class Draft:
    title: str
    text: str


@dataclass(frozen=True)
class Postcard:
    id: str
    epoch: int
    place: str
    province: str
    title: str
    text: str
    tone: str
    weather: Weather
    generated_at: str
    trigger: str
    model: str
