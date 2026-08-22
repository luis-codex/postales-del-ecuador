"""The public archive the web page reads.

The keys in this JSON are a contract with web/index.html.
"""

import json
from datetime import UTC, datetime

import boto3

KEY = "data/archive.json"


def _to_json(postcard):
    return {
        "id": postcard.id,
        "place": postcard.place,
        "province": postcard.province,
        "title": postcard.title,
        "text": postcard.text,
        "tone": postcard.tone,
        "weather": vars(postcard.weather),
        "generated_at": postcard.generated_at,
        "trigger": postcard.trigger,
    }


class S3Archive:
    def __init__(self, bucket, region):
        self._bucket = bucket
        self._s3 = boto3.client("s3", region_name=region)

    def publish(self, postcards):
        content = {
            "project": "Postales del Ecuador",
            "total": len(postcards),
            "updated_at": datetime.now(UTC).isoformat(),
            "postcards": [_to_json(postcard) for postcard in postcards],
        }
        self._s3.put_object(
            Bucket=self._bucket,
            Key=KEY,
            Body=json.dumps(content, ensure_ascii=False, indent=1).encode("utf-8"),
            ContentType="application/json; charset=utf-8",
            CacheControl="no-cache, max-age=0",
        )
        print(f"[s3] archive republished with {len(postcards)} postcards")
        return len(postcards)
