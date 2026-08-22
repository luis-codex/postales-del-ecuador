"""Adaptador de AWS Lambda.

Lo unico que hace es leer la configuracion del entorno, construir los
adaptadores y entregarselos al caso de uso. Toda la logica esta mas adentro.
"""

import os

from aplicacion.escribir_postal import EscribirPostal
from infraestructura.archivo_s3 import ArchivoS3
from infraestructura.catalogo_lugares import cargar as cargar_catalogo
from infraestructura.clima_open_meteo import ClimaOpenMeteo
from infraestructura.escritor_bedrock import EscritorBedrock
from infraestructura.memoria_dynamodb import MemoriaDynamoDB

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
MODEL_ID = os.environ.get("MODEL_ID", "amazon.nova-pro-v1:0")
REGION = os.environ.get("AWS_REGION", "us-east-1")

agente = EscribirPostal(
    catalogo=cargar_catalogo(),
    memoria=MemoriaDynamoDB(TABLE_NAME, REGION),
    clima=ClimaOpenMeteo(),
    escritor=EscritorBedrock(MODEL_ID, REGION),
    archivo=ArchivoS3(BUCKET_NAME, REGION),
)


def lambda_handler(event, context):
    origen = (event or {}).get("origen")
    disparador = "eventbridge-scheduler" if origen == "scheduler" else "invocacion-directa"
    return agente.ejecutar(disparador)
