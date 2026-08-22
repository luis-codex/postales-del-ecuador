# Checklist de entrega — Weekend Creative Agent Challenge

> Estado a 22 de agosto, 15:05 Ecuador. **Deadline: lunes 24 de agosto, 15:00 Ecuador.**
> Fuente de los requisitos: [términos y condiciones oficiales](https://builder.aws.com/content/3ICSgopf3Cc3xOtTPFKrULEtlyg/terms-and-conditions-weekend-challenge-set-your-creative-app-free)

---

## ✅ Categoría 1 — Completeness (puerta eliminatoria)

Un fallo aquí descalifica sin evaluar el resto.

| Requisito | Estado | Verificado |
|---|---|---|
| Artículo publicado en AWS Builder Center | ⬜ **PENDIENTE** | — lo tiene que hacer Luis |
| Publicado entre 21 ago 00:00 PT y 24 ago 13:00 PT | ⬜ pendiente | al publicar |
| Mínimo 500 palabras | ✅ **2.353** | contado |
| Título contiene `Weekend Creative Agent Challenge: Postales del Ecuador` | ✅ | en la cabecera de `ARTICULO.md` |
| Tag `agents` | ⬜ **paso aparte en el editor** | verificar en el artículo ya publicado |
| Sección *Vision & What It Does* | ✅ 417 palabras | |
| Sección *How You Built It* | ✅ 714 palabras | |
| Sección *AWS Services Used / Architecture Overview* | ✅ 507 palabras | |
| Sección *What You Learned* | ✅ 373 palabras | |
| Sección *Link to App or Repo* | ✅ 159 palabras | |
| Link a la app funcional | ✅ HTTP 200 | sin credenciales |
| Link al repo público | ✅ HTTP 200 | sin sesión |

## ✅ Categoría 2 — Relevance & Functionality

| Requisito | Estado | Evidencia |
|---|---|---|
| Es un agente always-on | ✅ | EventBridge Scheduler `ENABLED`, `cron(0 6 * * ? *)` |
| Produce output creativo | ✅ | 21 postales literarias, 20 lugares distintos |
| **Sin iniciación manual** | ✅ | la web no tiene ni un `<button>`, `<form>` ni `<input>` |
| Evidencia de generación autónoma | ✅ | 14 postales marcadas `eventbridge-scheduler` + `evidencia/cloudwatch-ejecuciones.txt` |
| Encaja con el prompt del challenge | ✅ | es literalmente *"an agent that themes its output to the day or weather"* |

## ✅ Categoría 3 — AWS Service Usage

| Requisito | Estado | |
|---|---|---|
| Desplegado en ≥1 servicio AWS | ✅ | se usan **9** |
| El artículo describe los servicios | ✅ | tabla dedicada en la sección de arquitectura |

Bedrock · Lambda · EventBridge Scheduler · DynamoDB · S3 · CloudWatch · SNS · X-Ray · IAM

---

## Lo que falta — solo esto

1. ⬜ **Publicar el artículo** en builder.aws.com desde tu cuenta
   - Copiar el título **literal** de la cabecera de `ARTICULO.md`
   - Añadir el tag `agents` — es un paso separado en el editor
   - **Verificar el tag en el artículo ya publicado**, no en el borrador
2. ⬜ **Comentar el link** de tu artículo en el [artículo del challenge](https://builder.aws.com/content/3HkL1H9G5DVm7ZtpO8EcOt6jZsV/weekend-challenge-set-your-creative-app-free)
   - No es obligatorio, pero es lo que da visibilidad para "Builder of the week"

---

## Después de publicar — no olvidar

- ⬜ **No borrar nada hasta el 15 de septiembre.** La evaluación llega hasta ~el 7 y un link
  roto ese día descalifica. `terraform destroy` puede esperar.
- ⬜ Reverificar los links el **25 de agosto** y el **1 de septiembre**
- ⬜ **Rotar las claves root de AWS** y crear un usuario IAM. Es lo único de todo el proyecto
  que es un problema de seguridad de verdad.
- ⬜ Opcional: suscribir tu correo a las alertas del agente
  ```bash
  cd infra/environments/prod
  aws sns subscribe --topic-arn "$(terraform output -raw tema_alertas)" \
    --protocol email --notification-endpoint tu@correo.com
  ```

---

## Estado técnico verificado

| | |
|---|---|
| Web pública | HTTP 200 · 21 postales · 20 lugares · 14 por scheduler |
| Repo público | HTTP 200 · 14 commits · sin el ID de cuenta en el historial |
| Terraform | sin deriva · build determinista |
| Pruebas | 17 pasando en 0,01 s, sin AWS ni red |
| Lambda | arm64 · X-Ray activo · <3 s por ejecución |
| Coste | céntimos — ~600 tokens de entrada y ~200 de salida por postal |
