"""Le pide la postal al modelo.

El prompt vive aqui y no en el dominio porque su forma la dicta Bedrock: el
ejemplo few-shot y la exigencia de responder solo con JSON son detalles del
modelo. Las reglas que cita si son del dominio, y se leen de alli.
"""

import json
import re
from datetime import datetime

from dominio.modelos import Borrador, Clima, Lugar, ZONA_ECUADOR
from dominio.sensaciones import describir, momento_del_dia

LUGARES_QUE_MENCIONA = 6

EJEMPLO = (
    '{"titulo": "Nadie levanta la vista", "postal": "La neblina se comio el volcan otra vez. '
    "Todos saben que sigue ahi, detras, pero hoy no le toca ser visto. En el mercado las senoras "
    "cubren las frutas con plastico y siguen conversando como si nada. El agua no cae, mas bien "
    "flota: se queda en el pelo, en las mangas, en el borde de las cosas. Un perro cruza la calle "
    "y deja huellas que duran medio minuto. Huele a lena mojada y a cascara de naranja. Cuando el "
    "aire esta asi de lleno de agua uno camina mirando el suelo, no por tristeza, sino porque el "
    'suelo es lo unico que se ve completo."}'
)


def _construir_prompt(lugar: Lugar, clima: Clima, tono: str, memoria) -> str:
    visitados = [p.lugar for p in memoria[:LUGARES_QUE_MENCIONA] if p.lugar]
    recuerdo = (
        f"\nYa escribiste desde: {', '.join(visitados)}. No repitas sus imagenes."
        if visitados else ""
    )
    ahora = datetime.now(ZONA_ECUADOR)

    return f"""Escribes una postal desde un lugar del Ecuador. Estas ahi ahora mismo y anotas lo que ves.

LUGAR: {lugar.nombre}, {lugar.provincia}
QUE HAY AHI: {lugar.alma}
CUANDO: {momento_del_dia(ahora, clima.es_de_dia)}

COMO SE SIENTE EL LUGAR AHORA MISMO:
{describir(clima)}

TONO DE HOY: {tono}{recuerdo}

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
{EJEMPLO}

Responde UNICAMENTE con el JSON: {{"titulo": "...", "postal": "..."}}"""


class EscritorBedrock:
    def __init__(self, modelo, region):
        import boto3
        self.modelo = modelo
        self._bedrock = boto3.client("bedrock-runtime", region_name=region)

    def escribir(self, lugar: Lugar, clima: Clima, tono: str, memoria, intento: int) -> Borrador:
        respuesta = self._bedrock.converse(
            modelId=self.modelo,
            messages=[{"role": "user", "content": [
                {"text": _construir_prompt(lugar, clima, tono, memoria)}]}],
            inferenceConfig={"maxTokens": 1200, "temperature": 0.9, "topP": 0.9},
        )
        texto = respuesta["output"]["message"]["content"][0]["text"]
        uso = respuesta.get("usage", {})
        print(f"[bedrock] intento {intento} modelo={self.modelo} "
              f"tokens_in={uso.get('inputTokens')} tokens_out={uso.get('outputTokens')}")

        encontrado = re.search(r"\{.*\}", texto, re.S)
        if not encontrado:
            print(f"[validacion] intento {intento}: no devolvio JSON")
            return None
        try:
            datos = json.loads(encontrado.group(0))
        except json.JSONDecodeError as error:
            print(f"[validacion] intento {intento}: JSON invalido ({error})")
            return None

        return Borrador(
            titulo=(datos.get("titulo") or "").strip(),
            texto=(datos.get("postal") or "").strip(),
        )
