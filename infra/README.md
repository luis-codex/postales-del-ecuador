# Infraestructura

Terraform. Módulos reutilizables en `modules/`, y un entorno que los compone en
`environments/prod/`.

```
infra/
├── bootstrap/                  crea el bucket del state · se aplica una vez
│   └── main.tf
├── modules/
│   ├── almacenamiento/         S3 + DynamoDB
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── agente/                 IAM + logs + Lambda + SNS + alarma
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── programacion/           IAM + EventBridge Scheduler
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    └── prod/
        ├── main.tf             une los módulos conectando sus salidas
        ├── providers.tf        provider AWS y etiquetas por defecto
        ├── backend.tf          state remoto
        ├── variables.tf
        ├── outputs.tf
        ├── terraform.tfvars    valores de este entorno
        └── backend.hcl.ejemplo
```

Los módulos no saben dónde están colocados en el repositorio: las rutas al código y al HTML
se calculan en `environments/prod/main.tf` desde `path.root` y se pasan como variables.

## Primera vez

El state vive en S3, pero ese bucket hay que crearlo con algo. Es el huevo y la gallina de
cualquier IaC, y se resuelve con un módulo aparte que usa state **local** y se aplica una
sola vez:

```bash
cd infra/bootstrap
terraform init && terraform apply
```

Después, el entorno:

```bash
cd infra/environments/prod
cp backend.hcl.ejemplo backend.hcl     # y pon el ID de tu cuenta
terraform init -backend-config=backend.hcl
terraform apply
```

`backend.hcl` está fuera del repositorio porque el nombre del bucket lleva el ID de la
cuenta. El backend de Terraform no admite variables, así que la única forma de no
publicarlo es la configuración parcial.

## Uso diario

```bash
cd infra/environments/prod

terraform plan                                     # qué cambiaría
terraform apply                                    # aplicarlo
terraform apply -var 'frecuencia=rate(5 minutes)'  # acelerar al agente
terraform output web_publica                       # la URL
terraform destroy                                  # desmontar todo
```

Cambiar el ritmo del agente no toca el código ni los datos: es una variable.

## Decisiones

**El state está bloqueado.** El backend de S3 usa `use_lockfile = true`, el bloqueo nativo
de S3. Antes esto exigía una tabla de DynamoDB aparte solo para los locks; desde Terraform
1.10 ya no. El bucket tiene versionado, así que un `apply` que corrompa el state se puede
revertir.

**Las etiquetas se ponen una vez.** `default_tags` en el provider etiqueta todos los
recursos. No hay un solo `tags = {...}` repetido en los módulos.

**El zip lo hace Terraform.** Un `data "archive_file"` empaqueta `src/` y su hash entra en
`source_code_hash`, así que cambiar el Python es suficiente para que el siguiente `apply`
suba el código nuevo. Sin scripts externos.

**La web es infraestructura.** `index.html` es un `aws_s3_object` con `etag = filemd5(...)`.
Si cambia el HTML, `terraform plan` lo detecta como cualquier otro cambio.

**Ojo con los ARN de las políticas gestionadas.** `AWSLambdaBasicExecutionRole` vive bajo
`service-role/` y `AWSXRayDaemonWriteAccess` no. Están escritos completos en el módulo del
agente en vez de construidos con un prefijo común, porque adivinarlo cuesta un `apply`
fallido.

## Qué trae

| | |
|---|---|
| Retención de logs | 30 días. Por defecto CloudWatch los guarda —y cobra— para siempre. |
| IAM acotado | `bedrock:InvokeModel` sobre el ARN del modelo concreto, nunca sobre `*`. |
| Alarma + SNS | Nadie mira los logs a las seis de la mañana. Si el agente falla, avisa. |
| arm64 (Graviton) | Mismo código, ~20% más barato. |
| AWS X-Ray | Trazas de cada ejecución. |
| PITR en DynamoDB | Recuperación puntual de la memoria del agente. |
| Etiquetas | Todos los recursos, vía `default_tags`. |
| Condición anti confused-deputy | El rol del scheduler solo lo asume esta cuenta. |

Para enterarte si el agente se rompe:

```bash
aws sns subscribe --topic-arn "$(terraform output -raw tema_alertas)" \
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

## Añadir un entorno

Copiar `environments/prod` a `environments/dev`, cambiar `nombre_bucket` y el `key` del
backend, y aplicar. Los módulos no cambian: para eso están.

## Lo que falta, dicho claro

- **La web va por HTTP.** Los endpoints de sitio estático de S3 no soportan TLS. La solución
  es CloudFront delante.
- **El `apply` se hace desde un portátil**, no desde un pipeline.
