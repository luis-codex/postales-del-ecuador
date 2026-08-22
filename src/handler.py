"""AWS Lambda adapter.

All it does is read the configuration from the environment, build the adapters
and hand them to the use case. Every decision lives further in.
"""

import os

from application.write_postcard import WritePostcard
from infrastructure.archive_s3 import S3Archive
from infrastructure.bedrock_writer import BedrockWriter
from infrastructure.memory_dynamodb import DynamoDBMemory
from infrastructure.places_catalog import load as load_catalog
from infrastructure.weather_open_meteo import OpenMeteoWeather

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
MODEL_ID = os.environ.get("MODEL_ID", "amazon.nova-pro-v1:0")
REGION = os.environ.get("AWS_REGION", "us-east-1")

agent = WritePostcard(
    catalog=load_catalog(),
    memory=DynamoDBMemory(TABLE_NAME, REGION),
    weather=OpenMeteoWeather(),
    writer=BedrockWriter(MODEL_ID, REGION),
    archive=S3Archive(BUCKET_NAME, REGION),
)


def lambda_handler(event, context):
    origin = (event or {}).get("origen")
    trigger = "eventbridge-scheduler" if origin == "scheduler" else "direct-invocation"
    return agent.execute(trigger)
