# factory-planner boilerpate (Boilerplate de Agente Inteligente)

Este repositorio es un **boilerplate (plantilla de inicio)** para construir agentes inteligentes orquestadores basados en ReAct utilizando el **Google Agent Development Kit (ADK)** y listos para interactuar mediante el protocolo **Agent-to-Agent (A2A)** y servidores **Model Context Protocol (MCP)** basándonos en el agente mostrado en la preparación del jueves 18.

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

## 🚀 Primeros Pasos en Google Cloud Shell Editor

> Estos pasos están pensados para ejecutarse íntegramente desde **Cloud Shell Editor** (editor.cloud.google.com). No necesitas instalar nada en tu máquina local.

### Paso 0 — Abre el proyecto en Cloud Shell Editor

1. Ve a [shell.cloud.google.com/cloudshell/editor](https://shell.cloud.google.com/cloudshell/editor)
2. Clona este repositorio en el terminal inferior:

```bash
git clone --branch boilerplate --single-branch https://github.com/irian-sanchez-dvt/showcase_agent.git
cd showcase_agent
```

3. En el menú **File → Open Folder**, abre la carpeta `showcase_agent` para verla en el explorador de ficheros.

---

### Paso 1 — Ejecuta el script de configuración

El script instala `uv`, `google-agents-cli`, crea el `.env` inicial y autentica tu sesión con GCP:

```bash
bash setup.sh
```

Cuando te pida login, sigue el enlace que aparece en el terminal y pega el código de verificación. Al terminar, activa el entorno virtual:

```bash
source .venv/bin/activate
```

---

### Paso 2 — Configura tus variables de entorno

El script ya ha creado el archivo `.env` a partir de `.env.example`. Ábrelo en el editor y rellena tus valores reales:

```bash
# En el terminal de Cloud Shell
nano .env
# O ábrelo directamente desde el explorador de ficheros del editor
```

Variables clave en `.env`:

| Variable | Descripción |
| :--- | :--- |
| `OFFLINE_MODE` | `true` para desarrollo local sin GCP, `false` para producción |
| `GOOGLE_CLOUD_PROJECT` | ID de tu proyecto de GCP (ej: `mi-proyecto-123`) |
| `MCP_SERVER_URL` | URL de tu servidor MCP desplegado en Cloud Run |
| `PARTNER_AGENT_URL` | URL del agente partner remoto (A2A) |
| `GCS_SKILLS_BUCKET` | Nombre del bucket GCS para habilidades y reportes |

> **Tip:** Para encontrar tu Project ID ejecuta `gcloud config get-value project`.

---

### Paso 3 — Prueba el agente en modo offline

Antes de desplegar nada en la nube, verifica que el agente arranca correctamente en modo local:

```bash
# Asegúrate de tener OFFLINE_MODE=true en tu .env
uv run adk web --port 8080 --allow_origins "regex:.*" .
```

Cloud Shell abrirá automáticamente una ventana de preview (o puedes hacer clic en el icono **Web Preview → Preview on port 8080**). Deberías ver el playground del ADK y poder chatear con el agente.

---

### Paso 4 — Despliega tu servidor MCP en Cloud Run

Con el agente funcionando en local, el siguiente paso es conectarlo a un servidor MCP real. Desde el terminal de Cloud Shell:

```bash
cd mcp-server
gcloud run deploy my-mcp-server \
  --source . \
  --region europe-west1 \
  --no-allow-unauthenticated
```

Cuando termine, copia la URL que aparece (`Service URL: https://my-mcp-server-xxxx.a.run.app`) y pégala en tu `.env`:

```env
MCP_SERVER_URL=https://my-mcp-server-xxxx.a.run.app
OFFLINE_MODE=false
```

Vuelve a la raíz del proyecto:

```bash
cd ..
```

> **Ejercicio:** Antes de desplegar, abre `mcp-server/index.js` y sustituye el `TODO: [EJERCICIO]` en `getGenericDataLive` por la lógica real de tu caso de uso.

---

### Paso 5 — Despliega el agente en Agent Runtime (GCP)

```bash
agents-cli deploy
```

Cuando el deploy termine, registra el agente en Gemini Enterprise para que tu equipo pueda usarlo:

```bash
agents-cli publish gemini-enterprise
```

---

## 🛠️ Comandos Útiles del Proyecto

| Comando | Descripción |
| :--- | :--- |
| `source .venv/bin/activate` | Activa el entorno virtual de Python en tu terminal. |
| `uv run adk run app` | **Inicia tu agente en modo consola interactiva** (puedes chatear con él directamente en la terminal). |
| `uv run adk web --port 8080 --allow_origins "regex:.*" .` | Lanza el Web UI interactivo (Playground visual) de la ADK en el puerto `8080`. |
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
