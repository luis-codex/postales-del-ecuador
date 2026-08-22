"""What to write today, decided from what has already been written.

This is the difference between an agent and a cron job with an API key: before
writing, it looks at its memory and deliberately picks something it has not
done. Without this layer, thirty days of postcards would be the same postcard
thirty times.

The catalog arrives as a parameter: where the places come from is none of the
domain's business.
"""

import random

from .models import Place

TONES = [
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

PLACES_REMEMBERED = 18
TONES_REMEMBERED = 8


def choose_place(memory, catalog) -> Place:
    recent = {postcard.place for postcard in memory[:PLACES_REMEMBERED]}
    available = [place for place in catalog if place.name not in recent]
    return random.choice(available or catalog)


def choose_tone(memory) -> str:
    used = {postcard.tone for postcard in memory[:TONES_REMEMBERED]}
    available = [tone for tone in TONES if tone not in used]
    return random.choice(available or TONES)
