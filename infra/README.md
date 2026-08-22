# Infraestructura

Todo el sistema es CloudFormation. No hay un solo recurso creado a mano.

```
infra/
├── main.yaml                    stack raíz: compone las tres capas
├── stacks/
│   ├── almacenamiento.yaml      capa 1 · S3 + DynamoDB
│   ├── agente.yaml              capa 2 · IAM + Lambda
│   └── programacion.yaml        capa 3 · IAM + EventBridge Scheduler
├── params/
│   └── prod.json                parámetros por entorno
├── scripts/
│   ├── deploy.sh                empaqueta y despliega
│   ├── frecuencia.sh            cambia cada cuánto despierta el agente
│   ├── invocar.sh               lo despierta a mano y muestra sus logs
│   └── evidencia.sh             lista cada vez que ha despertado y quién lo despertó
└── backup/                      volcados de la tabla antes de migraciones
```

## Por qué tres stacks y no uno

La guía de buenas prácticas de CloudFormation recomienda
[organizar los stacks por ciclo de vida y propiedad](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html).
Aquí las tres capas cambian a ritmos muy distintos:

| Capa | Contiene | Con qué frecuencia cambia |
|---|---|---|
| **almacenamiento** | El bucket público y la tabla de memoria | Casi nunca. Guarda las postales ya escritas. |
| **agente** | La Lambda y su rol | En cada despliegue de código. |
| **programacion** | El scheduler y su rol | Cuando se ajusta el ritmo del agente. |

Separarlas tiene una consecuencia práctica concreta: **cambiar cada cuánto escribe el
agente no toca ni el código ni los datos.** Durante el fin de semana del challenge el
scheduler corría cada pocos minutos para acumular archivo, y pasar al ritmo diario fue
actualizar una capa sola:

```bash
bash infra/scripts/frecuencia.sh "cron(0 6 * * ? *)"
```

Las dos capas de datos llevan `DeletionPolicy: Retain`. Borrar el stack no borra las
postales que el agente ya escribió — eso es suyo, no del despliegue.

## Cómo se despliega

```bash
bash infra/scripts/deploy.sh          # entorno prod por defecto
bash infra/scripts/deploy.sh staging  # usa infra/params/staging.json
```

El script hace tres cosas:

1. Crea, si no existe, un bucket de artefactos donde CloudFormation sube el código de la
   Lambda y las plantillas anidadas.
2. `aws cloudformation package` — resuelve los `TemplateURL` locales y el `Code: ../../src`,
   los sube y reescribe la plantilla con las URLs reales de S3.
3. `aws cloudformation deploy` — crea o actualiza el stack y publica la web.

Requiere AWS CLI configurado y acceso a Amazon Bedrock en la región. Nada más: ni SAM, ni
Terraform, ni CDK, ni bootstrap.

## Parámetros

`params/prod.json`:

| Parámetro | Qué controla |
|---|---|
| `NombreBucket` | Nombre global del bucket que sirve la web |
| `ModeloBedrock` | Modelo que escribe las postales |
| `Frecuencia` | Expresión `cron()` o `rate()` del scheduler |
| `ZonaHoraria` | Zona en la que se interpreta esa expresión |

Para un entorno nuevo basta con copiar el JSON, cambiarle el nombre del bucket y desplegar
con otro `STACK`:

```bash
STACK=postales-staging bash infra/scripts/deploy.sh staging
```

## Una excepción honesta

El log group `/aws/lambda/postales-del-ecuador` **no** está en las plantillas. Lo crea la
propia Lambda y se conservó al migrar desde el despliegue inicial porque contiene el
registro de las primeras ejecuciones autónomas del agente. Meterlo en el stack habría
obligado a borrarlo y recrearlo, y con él esa evidencia.
