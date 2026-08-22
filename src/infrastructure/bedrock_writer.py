"""Asks the model for the postcard.

The prompt lives here and not in the domain because Bedrock dictates its shape:
the few-shot example and the demand to answer with JSON only are details of the
model. The rules it cites do belong to the domain, and are read from there.

The prompt itself stays in Spanish: the product is Spanish-language postcards.
"""

import json
import re
from datetime import datetime

import boto3

from domain.models import ECUADOR_TZ, Draft, Place, Weather
from domain.sensations import describe, time_of_day

PLACES_MENTIONED = 6

EXAMPLE = (
    '{"titulo": "Nadie levanta la vista", "postal": "La neblina se comio el volcan otra vez. '
    "Todos saben que sigue ahi, detras, pero hoy no le toca ser visto. En el mercado las senoras "
    "cubren las frutas con plastico y siguen conversando como si nada. El agua no cae, mas bien "
    "flota: se queda en el pelo, en las mangas, en el borde de las cosas. Un perro cruza la calle "
    "y deja huellas que duran medio minuto. Huele a lena mojada y a cascara de naranja. Cuando el "
    "aire esta asi de lleno de agua uno camina mirando el suelo, no por tristeza, sino porque el "
    'suelo es lo unico que se ve completo."}'
)


def _build_prompt(place: Place, weather: Weather, tone: str, memory) -> str:
    visited = [p.place for p in memory[:PLACES_MENTIONED] if p.place]
    recollection = (
        f"\nYa escribiste desde: {', '.join(visited)}. No repitas sus imagenes."
        if visited else ""
    )
    now = datetime.now(ECUADOR_TZ)

    return f"""Escribes una postal desde un lugar del Ecuador. Estas ahi ahora mismo y anotas lo que ves.

LUGAR: {place.name}, {place.province}
QUE HAY AHI: {place.soul}
CUANDO: {time_of_day(now, weather.is_daytime)}

COMO SE SIENTE EL LUGAR AHORA MISMO:
{describe(weather)}

TONO DE HOY: {tone}{recollection}

REGLAS INNEGOCIABLES:
1. PROHIBIDO escribir numeros, grados, porcentajes o kilometros por hora. Ni uno.
   No describas el clima: hazlo notar a traves de lo que la gente y las cosas hacen.
2. PROHIBIDAS estas palabras: magico, magia, encanto, encantador, paraiso, joya,
   destino, imperdible, mistico, unico, maravilloso, hermoso, inolvidable.
3. El titulo NO puede contener el nombre del lugar ni de la provincia. Maximo 6 palabras.
   Debe ser una frase concreta sacada del texto, no un rotulo.
   MAL: "Manana fresca en Guaranda". BIEN: "Nadie levanta la vista".
4. Entre 95 y 125 palabras en "postal". Prosa corrida, sin saltos de linea.
5. Cosas concretas: objetos, oficios, animales, sonidos, olores, lo que hace la gente.
6. NO copies literalmente las frases de "QUE HAY AHI" ni el nombre del tono.
   Son contexto para ti, no material para pegar en el texto.
7. Espanol de Ecuador, natural. Sin exotizar el pais.

EJEMPLO DEL REGISTRO QUE BUSCO (otro lugar, otro dia):
{EXAMPLE}

Responde UNICAMENTE con el JSON: {{"titulo": "...", "postal": "..."}}"""


class BedrockWriter:
    def __init__(self, model, region):
        self.model = model
        self._bedrock = boto3.client("bedrock-runtime", region_name=region)

    def write(self, place: Place, weather: Weather, tone: str, memory,
              attempt: int) -> Draft | None:
        response = self._bedrock.converse(
            modelId=self.model,
            messages=[{"role": "user", "content": [
                {"text": _build_prompt(place, weather, tone, memory)}]}],
            inferenceConfig={"maxTokens": 1200, "temperature": 0.9, "topP": 0.9},
        )
        blocks = response.get("output", {}).get("message", {}).get("content", [])
        text = next((block["text"] for block in blocks if "text" in block), "")
        usage = response.get("usage", {})
        print(f"[bedrock] attempt {attempt} model={self.model} "
              f"tokens_in={usage.get('inputTokens')} tokens_out={usage.get('outputTokens')}")

        found = re.search(r"\{.*\}", text, re.DOTALL)
        if not found:
            print(f"[validation] attempt {attempt}: no JSON returned")
            return None
        try:
            data = json.loads(found.group(0))
        except json.JSONDecodeError as error:
            print(f"[validation] attempt {attempt}: invalid JSON ({error})")
            return None

        return Draft(
            title=(data.get("titulo") or "").strip(),
            text=(data.get("postal") or "").strip(),
        )
