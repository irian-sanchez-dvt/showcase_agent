# Guía de Despliegue y Registro en GCP (Gemini Enterprise)

Esta guía explica paso a paso cómo desplegar el agente `factory-planner` en **Agent Runtime (Vertex AI)** y cómo registrar sus capacidades (skills) en **Gemini Enterprise Agent Platform**.

---

## Prerrequisitos

1. **Autenticación en GCP:**
   ```bash
   gcloud auth login
   gcloud config set project dvt-sp-agentspace
   ```

2. **Login en el Agents CLI:**
   ```bash
   agents-cli login --interactive
   ```

---

## Paso 1: Despliegue en Agent Runtime

Para desplegar tu agente en el entorno administrado de Google Cloud (Agent Runtime), ejecuta el siguiente comando:

```bash
agents-cli deploy
```

### ¿Qué hace este comando?
- Empaqueta el código de tu agente en la carpeta `app/`.
- Lo despliega en **Vertex AI Reasoning Engines (Agent Runtime)** en la región configurada (`eu-west1`).
- Genera un archivo local llamado `deployment_metadata.json` que almacena el identificador único del recurso (por ejemplo, `projects/dvt-sp-agentspace/locations/eu-west1/reasoningEngines/123456789`).

---

## Paso 2: Registro en Gemini Enterprise (Publish)

Una vez que el agente esté desplegado, puedes registrarlo junto con sus "skills" o herramientas en la plataforma de Gemini Enterprise. 

Ejecuta el siguiente comando en modo interactivo:

```bash
agents-cli publish gemini-enterprise --interactive
```

O de forma directa en tu pipeline de CI/CD:

```bash
agents-cli publish gemini-enterprise \
  --gemini-enterprise-app-id projects/dvt-sp-agentspace/locations/global/collections/default_collection/engines/factory-planner-app \
  --display-name "Planificador de Fábrica" \
  --description "Agente experto en validar viabilidad de lotes de producción cruzando logística A2A, clima MCP y cronogramas." \
  --registration-type a2a
```

### ¿Qué skills o herramientas se registrarán?
Al registrar el agente, Gemini Enterprise expondrá las siguientes habilidades para que otros agentes de la organización o usuarios de Gemini Enterprise puedan invocarlas:

1. **`read_production_schedule`**: Skill de lectura local del cronograma de contenedores activos de la flota (con datos sincronizados de BigQuery).
2. **`query_logistics_agent`**: Skill de comunicación A2A con el agente de logística en Cloud Run para consultar detalles específicos del contenedor (contenido, peso, aduanas).
3. **`get_port_weather`**: Skill climática ejecutada a través del servidor MCP sobre Stdio para evaluar riesgos meteorológicos en los puertos de origen.

---

## Paso 3: Interconexión A2A con el Agente de Logística

Si el agente de logística remoto está desplegado en Cloud Run, puedes configurar su URL en las variables de entorno de tu agente para que la interconexión sea 100% interactiva. 

En producción, concede los permisos necesarios para la comunicación entre servicios:
```bash
gcloud run services add-iam-policy-binding logistics-agent-service \
  --member="serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
  --role="roles/run.servicesInvoker" \
  --region="eu-west1"
```
