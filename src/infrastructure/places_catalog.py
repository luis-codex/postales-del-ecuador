"""Loads the catalog of places from data/.

The fifty places are data, not rules: they live in a separate JSON file and this
adapter turns them into domain models. That way the domain receives the catalog
injected instead of importing it, and still depends on nothing.
"""

import json
from pathlib import Path

from domain.models import Place

PATH = Path(__file__).resolve().parent.parent / "data" / "places.json"


def load(path=PATH):
    with open(path, encoding="utf-8") as file:
        return [Place(**record) for record in json.load(file)]
