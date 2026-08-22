# Infraestructura

Bash modular. Un archivo de variables, una librería de utilidades, un script por capa,
y dos orquestadores que los cargan con `source`.

```
infra/
├── config.sh              todas las variables, y solo aquí
├── lib.sh                 utilidades: paso(), existe(), reintentar()
├── 10-almacenamiento.sh   bucket + tabla
├── 20-agente.sh           rol + logs + lambda + alarma
├── 30-programacion.sh     rol + scheduler
├── deploy.sh              orquesta el despliegue
├── destroy.sh             orquesta el desmontaje
├── frecuencia.sh          cambia el ritmo del agente
└── restaurar.sh           repuebla la memoria desde un respaldo
```

## Cómo se usa

```bash
bash infra/deploy.sh                            # crea o actualiza todo
FRECUENCIA="rate(5 minutes)" bash infra/deploy.sh   # con otra frecuencia
bash infra/frecuencia.sh "cron(0 6 * * ? *)"    # solo el reloj
bash infra/destroy.sh                           # avisa y no hace nada
bash infra/destroy.sh --si                      # desmonta de verdad
```

Requiere AWS CLI configurado y acceso a Amazon Bedrock en la región. Nada más.

## Cómo está montado

Cada capa expone dos funciones con el mismo patrón:

```bash
almacenamiento::desplegar()
almacenamiento::destruir()
```

`deploy.sh` las llama en orden; `destroy.sh` en orden inverso, para que lo que depende de
algo se borre antes que aquello de lo que depende. Los scripts de capa no se ejecutan
sueltos: se cargan con `source` y solo definen funciones.

Todo lo configurable vive en `config.sh` y en ningún otro sitio. Cualquier variable se puede
sobreescribir desde el entorno sin editar nada:

```bash
BUCKET=otro-bucket REGION=us-west-2 bash infra/deploy.sh
```

## Es idempotente

Volver a ejecutar `deploy.sh` no duplica nada. Cada recurso se comprueba antes de crearse,
con un helper que hace legible el patrón:

```bash
if existe aws dynamodb describe-table --table-name "$TABLA" --region "$REGION"; then
  salta "tabla $TABLA ya existe"
else
  ...
fi
```

La segunda pasada no crea nada: solo reaplica lo que es barato reaplicar — políticas,
retención, configuración del bucket — y actualiza el código de la Lambda.

## Qué hay que saber si vienes de una herramienta declarativa

Esto se escribió primero con CloudFormation y luego con SAM antes de acabar en bash. Las
diferencias que se notan al vivir con ello:

| | Aquí |
|---|---|
| **`destroy.sh` existe** | Un script sabe crear, no sabe destruir. El orden de borrado se mantiene a mano y hay que actualizarlo cada vez que se añade un recurso. Es el precio principal. |
| **La idempotencia se escribe** | El helper `existe()` es la respuesta a "¿esto ya está?", repetida por recurso. Una herramienta declarativa no cobra por esa pregunta. |
| **Sin rollback** | Si falla a la mitad, queda a medias. Por eso cada paso es idempotente: la recuperación es volver a lanzarlo. |
| **Quitar un recurso no lo borra** | Si borras un recurso del script, sigue vivo en AWS cobrando. Nadie avisa. |
| **La propagación de IAM se maneja a mano** | Un rol recién creado tarda segundos en ser usable. De ahí `reintentar 6 10 aws lambda create-function`. |
| **Las etiquetas, en tres formatos** | El AWS CLI las pide como mapa, como lista o como JSON según el servicio. Los tres están declarados juntos en `config.sh`. |

A cambio: todo está en un lenguaje que ya sabes leer, sin transform, sin estado y sin
ninguna capa entre lo que escribes y la llamada a la API.

## Qué trae

| | |
|---|---|
| Retención de logs | 30 días. Por defecto CloudWatch los guarda —y cobra— para siempre. |
| IAM acotado | `bedrock:InvokeModel` sobre el ARN del modelo concreto, nunca sobre `*`. |
| Alarma + SNS | Nadie mira los logs a las seis de la mañana. Si el agente falla, avisa. |
| arm64 (Graviton) | Mismo código, ~20% más barato. |
| AWS X-Ray | Trazas de cada ejecución. |
| PITR en DynamoDB | Recuperación puntual de la memoria del agente. |
| Etiquetas | Todos los recursos por proyecto y entorno. |

Para enterarte si el agente se rompe, suscribe tu correo:

```bash
aws sns subscribe --topic-arn "arn:aws:sns:us-east-1:<cuenta>:postales-del-ecuador-alertas" \
  --protocol email --notification-endpoint tu@correo.com
```

## Operar el agente a mano

Despertarlo ahora mismo y ver qué hizo:

```bash
aws lambda invoke --function-name postales-del-ecuador \
  --cli-binary-format raw-in-base64-out --payload '{}' \
  --log-type Tail --query LogResult --output text /dev/null | base64 -d
```

Ver cada vez que ha despertado y quién lo despertó — la evidencia de que corre solo:

```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/postales-del-ecuador \
  --filter-pattern '"[agente] despierta"' \
  --query 'events[].message' --output text | tr '\t' '\n'
```

## Lo que falta, dicho claro

- **La web va por HTTP.** Los endpoints de sitio estático de S3 no soportan TLS. La solución
  es CloudFront delante.
- **El despliegue se hace desde un portátil**, no desde un pipeline.
