"""La memoria del agente, guardada en DynamoDB.

Traduce entre la forma de la tabla y el modelo del dominio. El dominio no sabe
que 'clima_json' existe ni que el texto se guarda bajo la clave 'postal'.
"""

import json

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from dominio.modelos import Clima, Postal

LIMITE_LECTURA = 300


def _a_clima(crudo) -> Clima:
    datos = json.loads(crudo or "{}")
    return Clima(
        temperatura=float(datos.get("temperatura", 0)),
        humedad=int(datos.get("humedad", 0)),
        viento=float(datos.get("viento", 0)),
        descripcion=datos.get("descripcion", ""),
        codigo=int(datos.get("codigo", 0)),
        es_de_dia=bool(datos.get("es_de_dia", True)),
    )


def _a_postal(item) -> Postal:
    return Postal(
        id=item.get("id"),
        epoch=int(item.get("epoch", 0)),
        lugar=item.get("lugar"),
        provincia=item.get("provincia"),
        titulo=item.get("titulo"),
        texto=item.get("postal"),
        tono=item.get("tono"),
        clima=_a_clima(item.get("clima_json")),
        generada_en=item.get("generada_en"),
        disparador=item.get("disparador"),
        modelo=item.get("modelo"),
    )


def _a_item(postal: Postal):
    return {
        "id": postal.id,
        "epoch": postal.epoch,
        "lugar": postal.lugar,
        "provincia": postal.provincia,
        "titulo": postal.titulo,
        "postal": postal.texto,
        "tono": postal.tono,
        "clima_json": json.dumps(vars(postal.clima), ensure_ascii=False),
        "generada_en": postal.generada_en,
        "disparador": postal.disparador,
        "modelo": postal.modelo,
    }


class MemoriaDynamoDB:
    def __init__(self, nombre_tabla, region):
        self._tabla = boto3.resource("dynamodb", region_name=region).Table(nombre_tabla)

    def _todas_ordenadas(self):
        items = self._tabla.scan(Limit=LIMITE_LECTURA).get("Items", [])
        items.sort(key=lambda item: int(item.get("epoch", 0)), reverse=True)
        return [_a_postal(item) for item in items]

    def recientes(self, limite=20):
        try:
            return self._todas_ordenadas()[:limite]
        except (BotoCoreError, ClientError) as error:
            print(f"[memoria] no se pudo leer el historial: {error}")
            return []

    def todas(self, limite=120):
        return self._todas_ordenadas()[:limite]

    def guardar(self, postal: Postal):
        self._tabla.put_item(Item=_a_item(postal))
        print(f"[memoria] postal {postal.id} guardada")
