"""The rules a postcard must satisfy before it can be published.

Nobody reads what the agent writes at six in the morning, so the agent corrects
itself: if a draft breaks a rule it is discarded and asked for again.
"""

import re

from .models import Draft, Place

BANNED_WORDS = [
    "magic", "encant", "paraiso", "paraíso", "joya", "imperdible", "mistic", "místic",
    "maravillos", "hermos", "destino turistico", "destino turístico", "inolvidable",
]

MIN_WORDS = 85
MAX_WORDS = 145
MAX_TITLE_WORDS = 7


def review(draft: Draft, place: Place, tone: str) -> list:
    text = (draft.text or "").strip()
    title = (draft.title or "").strip()

    if not text:
        return ["empty postcard"]

    failures = []

    words = len(text.split())
    if not MIN_WORDS <= words <= MAX_WORDS:
        failures.append(f"length {words}")

    if re.search(r"\d", text):
        failures.append("contains digits")

    found = [word for word in BANNED_WORDS if word in text.lower()]
    if found:
        failures.append(f"banned words {found}")

    if not title:
        failures.append("empty title")
        return failures

    lowercase = title.lower()
    if (place.name.split(",")[0].lower() in lowercase
            or place.province.lower() in lowercase):
        failures.append("the title names the place")

    if len(title.split()) > MAX_TITLE_WORDS:
        failures.append("title too long")

    giveaways = [word for word in re.findall(r"\w{5,}", tone.lower()) if word in lowercase]
    if giveaways:
        failures.append(f"the title copies the tone {giveaways}")

    return failures
