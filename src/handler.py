"""Postales del Ecuador - el cerebro del agente.

Cada ejecucion, sin intervencion humana:
  1. Lee su memoria en DynamoDB (donde ya estuvo, con que tono ya escribio)
  2. Elige un lugar del Ecuador que no haya visitado recientemente
  3. Consulta el clima REAL de ese lugar ahora mismo (Open-Meteo)
  4. Traduce ese clima a sensaciones fisicas, nunca a numeros
  5. Escribe una postal literaria condicionada por lugar + clima + memoria (Bedrock)
  6. Valida el resultado y reintenta si no cumple
  7. Guarda la postal en su memoria y republica el archivo en S3

Sin dependencias fuera del runtime de Lambda: solo boto3 y urllib.
"""

import json
import os
import random
import re
import urllib.request
from datetime import datetime, timezone, timedelta

import boto3

from lugares import LUGARES, CODIGOS_CLIMA

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
MODEL_ID = os.environ.get("MODEL_ID", "amazon.nova-pro-v1:0")
REGION = os.environ.get("AWS_REGION", "us-east-1")

ECT = timezone(timedelta(hours=-5))  # hora de Ecuador

dynamodb = boto3.resource("dynamodb", region_name=REGION)
tabla = dynamodb.Table(TABLE_NAME)
bedrock = boto3.client("bedrock-runtime", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)

# El agente rota deliberadamente entre registros narrativos para no sonar igual
# todos los dias. Cual le toca se decide leyendo la memoria, no al azar.
TONOS = [
    "melancolico y contenido",
    "luminoso y agradecido",
    "seco y observacional, casi periodistico",
    "nostalgico de algo que no se nombra",
    "asombrado, como quien llega por primera vez",
    "intimo, dirigido a una segunda persona",
    "sobrio y geologico, atento al tiempo largo",
    "humoristico sin dejar de ser tierno",
    "inquieto, con algo de presagio",
    "sensorial y concreto, puro olor y textura",
    "reflexivo sobre el paso del tiempo",
    "callado, como una nota dejada sobre la mesa",
]

PALABRAS_PROHIBIDAS = [
    "magic", "encant", "paraiso", "paraíso", "joya", "imperdible", "mistic", "místic",
    "maravillos", "hermos", "destino turistico", "destino turístico", "inolvidable",
]

EJEMPLO = (
    '{"titulo": "Nadie levanta la vista", "postal": "La neblina se comio el volcan otra vez. '
    "Todos saben que sigue ahi, detras, pero hoy no le toca ser visto. En el mercado las senoras "
    "cubren las frutas con plastico y siguen conversando como si nada. El agua no cae, mas bien "
    "flota: se queda en el pelo, en las mangas, en el borde de las cosas. Un perro cruza la calle "
    "y deja huellas que duran medio minuto. Huele a lena mojada y a cascara de naranja. Cuando el "
    "aire esta asi de lleno de agua uno camina mirando el suelo, no por tristeza, sino porque el "
    'suelo es lo unico que se ve completo."}'
)


def leer_memoria(limite=20):
    """Recupera las ultimas postales. Esta es la memoria del agente."""
    try:
        items = tabla.scan(Limit=300).get("Items", [])
        items.sort(key=lambda x: int(x.get("epoch", 0)), reverse=True)
        return items[:limite]
    except Exception as e:
        print(f"[memoria] no se pudo leer el historial: {e}")
        return []


def elegir_lugar(memoria):
    """Elige un lugar evitando los visitados recientemente."""
    recientes = {m.get("lugar") for m in memoria[:18]}
    disponibles = [l for l in LUGARES if l["nombre"] not in recientes]
    if not disponibles:  # ya recorrio el pais entero: vuelve a empezar
        disponibles = LUGARES
    return random.choice(disponibles)


def elegir_tono(memoria):
    """Elige un registro narrativo que no se haya usado ultimamente."""
    usados = {m.get("tono") for m in memoria[:8]}
    disponibles = [t for t in TONOS if t not in usados]
    return random.choice(disponibles or TONOS)


def consultar_clima(lugar):
    """Clima real del lugar, ahora mismo. Open-Meteo, sin API key."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lugar['lat']}&longitude={lugar['lon']}"
        "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,is_day"
        "&timezone=America%2FGuayaquil"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "postales-del-ecuador/1.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        c = json.loads(r.read().decode())["current"]
    codigo = int(c.get("weather_code", 0))
    return {
        "temperatura": round(float(c.get("temperature_2m", 0)), 1),
        "humedad": int(c.get("relative_humidity_2m", 0)),
        "viento": round(float(c.get("wind_speed_10m", 0)), 1),
        "descripcion": CODIGOS_CLIMA.get(codigo, "cielo variable"),
        "codigo": codigo,
        "es_de_dia": bool(c.get("is_day", 1)),
    }


def traducir_a_sensaciones(clima):
    """Convierte los datos del clima en sensaciones fisicas.

    Es la pieza clave del agente: al modelo nunca se le muestra un numero, asi que
    no puede recitarlo. Solo puede escribir sobre como se siente estar ahi.
    """
    t, h, v = clima["temperatura"], clima["humedad"], clima["viento"]

    if t < 0:
        cuerpo = "frio que corta la cara y entumece los dedos"
    elif t < 8:
        cuerpo = "frio de paramo, de meter las manos en los bolsillos"
    elif t < 14:
        cuerpo = "fresco, se agradece una chompa"
    elif t < 19:
        cuerpo = "templado, ni frio ni calor"
    elif t < 24:
        cuerpo = "tibio, comodo en manga corta"
    elif t < 29:
        cuerpo = "calor, la sombra se vuelve importante"
    else:
        cuerpo = "calor pesado, de buscar donde sentarse quieto"

    if h >= 85:
        aire = "aire saturado, todo lo que se toca esta un poco mojado"
    elif h >= 70:
        aire = "aire humedo, la ropa tarda en secarse"
    elif h >= 50:
        aire = "aire normal"
    else:
        aire = "aire seco, los labios se parten"

    if v < 5:
        viento = "sin viento, el aire quieto"
    elif v < 15:
        viento = "brisa suave"
    elif v < 30:
        viento = "viento constante que no para"
    else:
        viento = "viento fuerte, cuesta caminar derecho"

    if t >= 24 and h >= 70:
        extra = " Se suda sin moverse."
    elif t < 8 and h >= 80:
        extra = " El frio es humedo, entra hasta los huesos."
    else:
        extra = ""

    return (
        f"- En el cuerpo: {cuerpo}\n"
        f"- El aire: {aire}\n"
        f"- El viento: {viento}\n"
        f"- El cielo: {clima['descripcion']}.{extra}"
    )


def momento_del_dia(ahora, es_de_dia):
    h = ahora.hour
    if not es_de_dia:
        return "de noche"
    if h < 7:
        return "al amanecer"
    if h < 12:
        return "por la manana"
    if h < 15:
        return "al mediodia"
    if h < 19:
        return "por la tarde"
    return "al anochecer"


def construir_prompt(lugar, clima, tono, memoria):
    visitados = [m.get("lugar") for m in memoria[:6] if m.get("lugar")]
    mem = (
        f"\nYa escribiste desde: {', '.join(visitados)}. No repitas sus imagenes."
        if visitados else ""
    )
    ahora = datetime.now(ECT)

    return f"""Escribes una postal desde un lugar del Ecuador. Estas ahi ahora mismo y anotas lo que ves.

LUGAR: {lugar['nombre']}, {lugar['provincia']}
QUE HAY AHI: {lugar['alma']}
CUANDO: {momento_del_dia(ahora, clima['es_de_dia'])}

COMO SE SIENTE EL LUGAR AHORA MISMO:
{traducir_a_sensaciones(clima)}

TONO DE HOY: {tono}{mem}

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


def validar(datos, lugar, tono):
    """Devuelve la lista de reglas incumplidas. Vacia = postal aceptada."""
    fallos = []
    titulo = (datos.get("titulo") or "").strip()
    postal = (datos.get("postal") or "").strip()

    if not postal:
        return ["postal vacia"]
    palabras = len(postal.split())
    if not 85 <= palabras <= 145:
        fallos.append(f"longitud {palabras}")
    if re.search(r"\d", postal):
        fallos.append("contiene numeros")
    bajo = postal.lower()
    encontradas = [p for p in PALABRAS_PROHIBIDAS if p in bajo]
    if encontradas:
        fallos.append(f"palabras prohibidas {encontradas}")
    if not titulo:
        fallos.append("titulo vacio")
    else:
        tbajo = titulo.lower()
        if lugar["nombre"].split(",")[0].lower() in tbajo or lugar["provincia"].lower() in tbajo:
            fallos.append("el titulo nombra el lugar")
        if len(titulo.split()) > 7:
            fallos.append("titulo demasiado largo")
        # el titulo no puede delatar la etiqueta del tono que le tocó
        filtradas = [w for w in re.findall(r"\w{5,}", tono.lower()) if w in tbajo]
        if filtradas:
            fallos.append(f"el titulo copia el tono {filtradas}")
    return fallos


def generar_postal(lugar, clima, tono, memoria, intentos=3):
    """Genera y valida. Reintenta si el modelo incumple las reglas."""
    prompt = construir_prompt(lugar, clima, tono, memoria)
    ultimo = None

    for intento in range(1, intentos + 1):
        resp = bedrock.converse(
            modelId=MODEL_ID,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 1200, "temperature": 0.9, "topP": 0.9},
        )
        texto = resp["output"]["message"]["content"][0]["text"]
        uso = resp.get("usage", {})
        print(f"[bedrock] intento {intento} modelo={MODEL_ID} "
              f"tokens_in={uso.get('inputTokens')} tokens_out={uso.get('outputTokens')}")

        m = re.search(r"\{.*\}", texto, re.S)
        if not m:
            print(f"[validacion] intento {intento}: no devolvio JSON")
            continue
        try:
            datos = json.loads(m.group(0))
        except json.JSONDecodeError as e:
            print(f"[validacion] intento {intento}: JSON invalido ({e})")
            continue

        fallos = validar(datos, lugar, tono)
        ultimo = datos
        if not fallos:
            print(f"[validacion] intento {intento}: postal aceptada")
            return datos
        print(f"[validacion] intento {intento} rechazado: {', '.join(fallos)}")

    if ultimo and ultimo.get("postal"):
        print("[validacion] se agotaron los intentos, se publica el mejor disponible")
        return ultimo
    raise ValueError("el modelo no produjo una postal utilizable en ningun intento")


def republicar_archivo():
    """Reconstruye el archivo publico desde la memoria y lo sube a S3."""
    items = tabla.scan(Limit=300).get("Items", [])
    items.sort(key=lambda x: int(x.get("epoch", 0)), reverse=True)

    postales = [{
        "id": it.get("id"),
        "lugar": it.get("lugar"),
        "provincia": it.get("provincia"),
        "titulo": it.get("titulo"),
        "postal": it.get("postal"),
        "tono": it.get("tono"),
        "clima": json.loads(it.get("clima_json", "{}")),
        "generada_en": it.get("generada_en"),
        "disparador": it.get("disparador"),
    } for it in items[:120]]

    archivo = {
        "proyecto": "Postales del Ecuador",
        "total": len(postales),
        "actualizado": datetime.now(timezone.utc).isoformat(),
        "postales": postales,
    }
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key="data/archive.json",
        Body=json.dumps(archivo, ensure_ascii=False, indent=1).encode("utf-8"),
        ContentType="application/json; charset=utf-8",
        CacheControl="no-cache, max-age=0",
    )
    print(f"[s3] archivo republicado con {len(postales)} postales")
    return len(postales)


def lambda_handler(event, context):
    event = event or {}
    disparador = "eventbridge-scheduler" if event.get("origen") == "scheduler" else "invocacion-directa"
    ahora = datetime.now(ECT)
    print(f"[agente] despierta. disparador={disparador} hora_ecuador={ahora.isoformat()}")

    memoria = leer_memoria()
    print(f"[memoria] {len(memoria)} postales previas en el historial")

    lugar = elegir_lugar(memoria)
    tono = elegir_tono(memoria)
    print(f"[decision] lugar={lugar['nombre']} tono={tono}")

    clima = consultar_clima(lugar)
    print(f"[clima] {lugar['nombre']}: {clima['temperatura']}C, {clima['descripcion']}, "
          f"humedad {clima['humedad']}%, viento {clima['viento']}km/h")

    datos = generar_postal(lugar, clima, tono, memoria)

    postal_id = ahora.strftime("%Y-%m-%dT%H-%M-%S")
    item = {
        "id": postal_id,
        "epoch": int(ahora.timestamp()),
        "lugar": lugar["nombre"],
        "provincia": lugar["provincia"],
        "titulo": datos.get("titulo", "Sin titulo").strip(),
        "postal": datos["postal"].strip(),
        "tono": tono,
        "clima_json": json.dumps(clima, ensure_ascii=False),
        "generada_en": ahora.isoformat(),
        "disparador": disparador,
        "modelo": MODEL_ID,
    }
    tabla.put_item(Item=item)
    print(f"[memoria] postal {postal_id} guardada")

    total = republicar_archivo()
    print(f"[agente] listo. '{item['titulo']}' desde {lugar['nombre']}. archivo: {total} postales")

    return {
        "statusCode": 200,
        "postal_id": postal_id,
        "lugar": lugar["nombre"],
        "titulo": item["titulo"],
        "total_archivo": total,
    }
