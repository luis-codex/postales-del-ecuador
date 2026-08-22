"""The agent's memory, stored in DynamoDB.

Translates between the table's shape and the domain model. The domain does not
know that 'weather_json' exists.
"""

import json
from decimal import Decimal

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from domain.models import Postcard, Weather

READ_LIMIT = 300


def _as_int(value) -> int:
    if isinstance(value, (int, float, Decimal, str)):
        return int(value)
    return 0


def _as_text(value) -> str:
    return value if isinstance(value, str) else ""


def _to_weather(raw) -> Weather:
    data = json.loads(_as_text(raw) or "{}")
    return Weather(
        temperature=float(data.get("temperature", 0)),
        humidity=int(data.get("humidity", 0)),
        wind=float(data.get("wind", 0)),
        description=data.get("description", ""),
        code=int(data.get("code", 0)),
        is_daytime=bool(data.get("is_daytime", True)),
    )


def _to_postcard(item) -> Postcard:
    return Postcard(
        id=_as_text(item.get("id")),
        epoch=_as_int(item.get("epoch", 0)),
        place=_as_text(item.get("place")),
        province=_as_text(item.get("province")),
        title=_as_text(item.get("title")),
        text=_as_text(item.get("text")),
        tone=_as_text(item.get("tone")),
        weather=_to_weather(item.get("weather_json")),
        generated_at=_as_text(item.get("generated_at")),
        trigger=_as_text(item.get("trigger")),
        model=_as_text(item.get("model")),
    )


def _to_item(postcard: Postcard):
    return {
        "id": postcard.id,
        "epoch": postcard.epoch,
        "place": postcard.place,
        "province": postcard.province,
        "title": postcard.title,
        "text": postcard.text,
        "tone": postcard.tone,
        "weather_json": json.dumps(vars(postcard.weather), ensure_ascii=False),
        "generated_at": postcard.generated_at,
        "trigger": postcard.trigger,
        "model": postcard.model,
    }


class DynamoDBMemory:
    def __init__(self, table_name, region):
        self._table = boto3.resource("dynamodb", region_name=region).Table(table_name)

    def _all_sorted(self):
        items = self._table.scan(Limit=READ_LIMIT).get("Items", [])
        items.sort(key=lambda item: _as_int(item.get("epoch", 0)), reverse=True)
        return [_to_postcard(item) for item in items]

    def recent(self, limit=20):
        try:
            return self._all_sorted()[:limit]
        except (BotoCoreError, ClientError) as error:
            print(f"[memory] could not read the history: {error}")
            return []

    def all(self, limit=120):
        return self._all_sorted()[:limit]

    def save(self, postcard: Postcard):
        self._table.put_item(Item=_to_item(postcard))
        print(f"[memory] postcard {postcard.id} saved")
