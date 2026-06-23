# factory-planner (Boilerplate de Agente Inteligente)

Este repositorio es un **boilerplate (plantilla de inicio)** para construir agentes inteligentes orquestadores basados en ReAct utilizando el **Google Agent Development Kit (ADK)** y listos para interactuar mediante el protocolo **Agent-to-Agent (A2A)** y servidores **Model Context Protocol (MCP)**.

Está diseñado específicamente como un esqueleto inicial para talleres y sesiones de aprendizaje, listo para ser desplegado y ejecutado en **Google Cloud Shell Editor**.

---

## ¿Qué hace este agente?

`factory_planner` es un agente experto genérico diseñado como una plantilla estructurada de ReAct. Su toma de decisiones demuestra la combinación de tres coordenadas de información que los asistentes del taller pueden expandir:

1.  **Herramientas Locales a Medida (`generic_tool`):** Una función local de Python que, en su estado inicial, resume texto de forma extractiva. **Es el principal punto de ejercicio del taller:** debes sustituir su lógica por la herramienta personalizada de tu agente (llamada a una API, cálculo, consulta a base de datos, etc.).
2.  **Servidor MCP Remoto (`generic_mcp_tool`):** Llama a **tu propio servidor MCP** desplegado en Cloud Run para realizar consultas estructuradas de forma segura. Debes desplegar el servidor incluido en `mcp-server/` (o el tuyo propio) y apuntar la variable `MCP_SERVER_URL` a su URL.
3.  **Colaboración Remota vía A2A (`partner_agent`):** Utiliza la interconexión nativa de A2A de Google ADK para comunicarse de manera remota con otros agentes del ecosistema y delegar tareas especializadas de forma transparente.

---

## 📁 Estructura del Proyecto y Carpetas

A continuación se detalla qué contiene cada carpeta del proyecto y para qué sirve en el desarrollo de tu agente:

### 1. `app/` (Código Principal del Agente)
Esta es la carpeta más importante, donde residirá toda la lógica de inteligencia de tu agente:
*   `agent.py`: El punto de entrada principal. Aquí se definen las instrucciones de comportamiento (prompt del sistema), se registran los callbacks de observabilidad, se cargan los esquemas A2A y se instancian las herramientas del agente. **Contiene un `TODO: [EJERCICIO]` en `generic_tool` y en el servidor MCP listo para que lo personalices.**
*   `agent_runtime_app.py`: Archivo estándar que actúa como envoltorio (wrapper) de FastAPI. Es necesario para empaquetar tu agente y permitir que se ejecute en **Agent Runtime (Reasoning Engines)** en Google Cloud de forma serverless.
*   `partner_agent_card.json`: Fichero de manifiesto (Agent Card) en formato JSON. Describe las capacidades y los endpoints de conexión de un agente externo con el que tu agente puede hablar de forma nativa a través de A2A. **Actualiza la URL con la de tu agente partner.**

### 2. `skills/` (Directorio de Habilidades Dinámicas)
*   Contiene manuales e instrucciones expertas escritas en Markdown (ej: `weather_report_skill.md`).
*   **¿Para qué sirve?** El agente lee dinámicamente estos archivos (vía GCS o disco local) en caliente durante la inicialización del chat y los inyecta en su prompt. Esto permite actualizar o añadir nuevas destrezas al agente en tiempo real sin redesplegar código.

### 3. `mcp-server/` (Servidor MCP — Despliégalo tú)
*   Implementa un servidor de **Model Context Protocol (MCP)** desarrollado en **Node.js** que se comunica vía HTTP/SSE utilizando JSON-RPC 2.0.
*   **Tienes que desplegarlo tú** en Cloud Run (u otro servicio) y configurar su URL en la variable `MCP_SERVER_URL` de tu `.env`. El servidor incluido es una plantilla funcional con un `TODO: [EJERCICIO]` para que sustituyas la lógica de consulta por la de tu caso de uso.
*   También puedes apuntar `MCP_SERVER_URL` a cualquier servidor MCP externo compatible.

### 4. Archivos en la Raíz del Proyecto
*   `setup.sh`: Script que prepara todo tu entorno de desarrollo en un solo paso (instalación de `uv`, `google-agents-cli`, dependencias del proyecto y login en GCP).
*   `pyproject.toml` y `uv.lock`: Definen los requisitos del sistema y las dependencias de Python administradas por `uv`.
*   `.env.example`: Plantilla de variables de entorno. Cópiala a `.env` y rellena tus valores reales.

---

## 🚀 Primeros Pasos

### 1. Configuración del entorno

```bash
bash setup.sh
source .venv/bin/activate
```

### 2. Configura tus variables de entorno

Copia la plantilla y rellena tus valores:

```bash
cp .env.example .env
```

Variables clave en `.env`:

| Variable | Descripción |
| :--- | :--- |
| `OFFLINE_MODE` | `true` para desarrollo local sin GCP, `false` para producción |
| `GOOGLE_CLOUD_PROJECT` | ID de tu proyecto de GCP |
| `MCP_SERVER_URL` | URL de tu servidor MCP desplegado en Cloud Run |
| `PARTNER_AGENT_URL` | URL del agente partner remoto (A2A) |
| `GCS_SKILLS_BUCKET` | Nombre del bucket GCS para habilidades y reportes |

### 3. Despliega tu servidor MCP

El servidor MCP incluido en `mcp-server/` es tu punto de partida. Despliégalo en Cloud Run:

```bash
cd mcp-server
gcloud run deploy my-mcp-server \
  --source . \
  --region europe-west1 \
  --no-allow-unauthenticated
```

Una vez desplegado, copia la URL generada y ponla en `MCP_SERVER_URL` de tu `.env`.

> **Ejercicio:** Abre `mcp-server/index.js` y busca el `TODO: [EJERCICIO]` en la función `getGenericDataLive`. Sustituye la lógica de ejemplo por la tuya (llamada a una API real, base de datos, etc.).

---

## 🛠️ Comandos Útiles del Proyecto

| Comando | Descripción |
| :--- | :--- |
| `source .venv/bin/activate` | Activa el entorno virtual de Python en tu terminal. |
| `uv run adk run app` | **Inicia tu agente en modo consola interactiva** (puedes chatear con él directamente en la terminal). |
| `uv run adk web --port 8080 .` | Lanza el Web UI interactivo (Playground visual) de la ADK en el puerto `8080`. |
| `agents-cli deploy` | Empaqueta y despliega tu agente en **Agent Runtime** de Google Cloud. |
| `agents-cli publish gemini-enterprise` | Registra el agente en la consola de **Gemini Enterprise** para que tu equipo pueda usarlo. |

---

## 🔧 Dónde personalizar tu agente

Hay tres puntos marcados con `TODO: [EJERCICIO]` en el código:

### 1. `app/agent.py` — `generic_tool` (herramienta local)
Esta función recibe un texto y actualmente devuelve un resumen extractivo básico. **Sustitúyela por la lógica de tu herramienta personalizada.**

```python
def generic_tool(param: str) -> str:
    # TODO: [EJERCICIO] Sustituye esta implementación por la lógica de tu agente.
    ...
```

### 2. `mcp-server/index.js` — `getGenericDataLive` (herramienta MCP remota)
Esta función es la que el servidor MCP ejecuta cuando el agente invoca `generic_mcp_tool`. Actualmente devuelve datos de ejemplo. **Conéctala a tu API o base de datos real.**

```javascript
async function getGenericDataLive(query) {
  // TODO: [EJERCICIO] Implementar la consulta a una API real o base de datos.
  ...
}
```

### 3. `app/agent.py` — `base_instruction` (prompt del sistema)
El prompt que define el comportamiento del agente. **Adáptalo al dominio de tu caso de uso.**

---

## 📡 Modo Offline / Local-First (Desarrollo Rápido)

Este boilerplate está preparado para ejecutarse en modo **Local-First**, permitiéndote probar todo el flujo de comportamiento de manera local y offline, sin necesidad de conectarse a internet o configurar credenciales de Google Cloud inicialmente.

Para activarlo, asegúrate de tener configurado en tu archivo `.env` local:
```env
OFFLINE_MODE=true
```
Esto redirigirá la descarga de habilidades al disco local y simulará consultas al servidor MCP sin conexión de red.
