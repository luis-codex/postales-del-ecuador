"""El archivo publico que lee la web.

Las claves de este JSON son contrato con web/index.html: el texto sale como
'postal' aunque el modelo del dominio lo llame 'texto'.
"""

import json
from datetime import datetime, timezone

import boto3

CLAVE = "data/archive.json"


def _a_json(postal):
    return {
        "id": postal.id,
        "lugar": postal.lugar,
        "provincia": postal.provincia,
        "titulo": postal.titulo,
        "postal": postal.texto,
        "tono": postal.tono,
        "clima": vars(postal.clima),
        "generada_en": postal.generada_en,
        "disparador": postal.disparador,
    }


class ArchivoS3:
    def __init__(self, bucket, region):
        self._bucket = bucket
        self._s3 = boto3.client("s3", region_name=region)

    def publicar(self, postales):
        contenido = {
            "proyecto": "Postales del Ecuador",
            "total": len(postales),
            "actualizado": datetime.now(timezone.utc).isoformat(),
            "postales": [_a_json(postal) for postal in postales],
        }
        self._s3.put_object(
            Bucket=self._bucket,
            Key=CLAVE,
            Body=json.dumps(contenido, ensure_ascii=False, indent=1).encode("utf-8"),
            ContentType="application/json; charset=utf-8",
            CacheControl="no-cache, max-age=0",
        )
        print(f"[s3] archivo republicado con {len(postales)} postales")
        return len(postales)
