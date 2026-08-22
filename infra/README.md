# Infraestructura

Todo el sistema es **AWS SAM** desplegado con CloudFormation. No hay un solo recurso creado
a mano — ni siquiera el bucket de artefactos.

```
infra/
├── template.yaml       SAM · toda la infraestructura (185 líneas)
├── bootstrap.yaml      el bucket de artefactos · se despliega una vez
├── params/prod.json    parámetros por entorno
└── scripts/
    ├── deploy.sh       empaqueta y despliega
    ├── frecuencia.sh   cambia cada cuánto despierta el agente
    └── restaurar.sh    repuebla la memoria desde un respaldo
```

Los `.sh` **no crean infraestructura**. `deploy.sh` es un envoltorio de `aws cloudformation
package` + `deploy`; los otros dos son herramientas de operación. Los recursos están
declarados en las dos plantillas.

Hubo un tercer y un cuarto script, `invocar.sh` y `evidencia.sh`. Cada uno envolvía un solo
comando de AWS, así que no eran scripts: eran alias con ínfulas. Los comandos están más
abajo, que es donde tenían que estar.

## Por qué SAM y no CloudFormation crudo

Esta es una aplicación serverless, y para eso SAM existe. `AWS::Serverless::Function`
resuelve en un bloque lo que en CloudFormation puro son cuatro recursos sueltos: la función,
su rol de ejecución, los permisos y el scheduler que la despierta.

Concretamente, esto:

```yaml
Events:
  Despertador:
    Type: ScheduleV2
    Properties:
      ScheduleExpression: !Ref Frecuencia
      Input: '{"origen":"scheduler"}'
```

sustituye a un `AWS::Scheduler::Schedule`, un `AWS::IAM::Role` para el scheduler y su
política de invocación. Y las `Policies:` de SAM (`DynamoDBCrudPolicy`, `S3WritePolicy`)
generan permisos acotados sin escribir el JSON de IAM a mano.

**No hace falta instalar SAM CLI.** Una plantilla SAM es CloudFormation con un transform que
se expande en el servidor; el AWS CLI la despliega con `CAPABILITY_AUTO_EXPAND`.

## Una vuelta atrás que vale la pena contar

La primera versión de esta carpeta tenía un stack raíz y tres stacks anidados —
almacenamiento, agente y programación — separados por ciclo de vida, siguiendo la
[guía de buenas prácticas de CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html).
El argumento era correcto en abstracto y estaba mal aplicado: **son siete recursos.**

Los stacks anidados cuestan tiempo de despliegue y dolor al depurar, y la regla real es
dividir cuando duele, no antes. Se colapsó todo en una plantilla SAM y el resultado son
menos líneas, menos indirección y capacidades que antes no estaban.

## Qué trae que la versión anterior no tenía

| | Por qué |
|---|---|
| **Retención de logs** | Por defecto CloudWatch los guarda para siempre, y se pagan para siempre. Aquí, 30 días. |
| **IAM acotado al modelo** | Antes era `bedrock:InvokeModel` sobre `*`. Ahora sobre el ARN del modelo concreto. |
| **Alarma de fallo + SNS** | Nadie mira los logs a las seis de la mañana. Si el agente falla, avisa. |
| **arm64 (Graviton)** | Mismo código, ~20% más barato. |
| **AWS X-Ray** | Trazas de cada ejecución, para ver dónde se va el tiempo. |
| **PITR en DynamoDB** | Recuperación puntual de la memoria del agente. |
| **Etiquetas** | Todo el stack etiquetado por proyecto y entorno. |
| **Bootstrap declarativo** | El bucket de artefactos también es una plantilla, no dos comandos sueltos. |

Las dos capas de datos llevan `DeletionPolicy: Retain`. Borrar el stack no borra las postales
que el agente ya escribió — eso es suyo, no del despliegue.

## Cómo se despliega

```bash
bash infra/scripts/deploy.sh          # entorno prod por defecto
bash infra/scripts/deploy.sh staging  # usa infra/params/staging.json
```

Requiere AWS CLI configurado y acceso a Amazon Bedrock en la región. Nada más: ni SAM CLI,
ni Terraform, ni CDK, ni bootstrap manual.

Cambiar el ritmo del agente no toca ni el código ni los datos:

```bash
bash infra/scripts/frecuencia.sh "cron(0 6 * * ? *)"
```

Para enterarte si el agente se rompe, suscribe tu correo al tema de alertas:

```bash
aws sns subscribe --topic-arn "$(aws cloudformation describe-stacks \
  --stack-name postales-del-ecuador \
  --query "Stacks[0].Outputs[?OutputKey=='TemaAlertas'].OutputValue" --output text)" \
  --protocol email --notification-endpoint tu@correo.com
```

## Lo que falta, dicho claro

- **La web va por HTTP.** Los endpoints de sitio estático de S3 no soportan TLS. La solución
  es CloudFront delante.
- **El despliegue se hace desde un portátil**, no desde un pipeline.

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
