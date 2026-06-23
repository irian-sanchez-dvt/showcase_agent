# factory-planner (Boilerplate de Agente Inteligente)

Este repositorio es un **boilerplate (plantilla de inicio)** para construir agentes inteligentes orquestadores basados en ReAct utilizando el **Google Agent Development Kit (ADK)** y listos para interactuar mediante el protocolo **Agent-to-Agent (A2A)** y servidores **Model Context Protocol (MCP)**.

Está diseñado específicamente como un esqueleto inicial para talleres y sesiones de aprendizaje, listo para ser desplegado y ejecutado en **Google Cloud Shell Editor**.

---

## ¿Qué hace este agente?

`factory_planner` es un agente experto genérico diseñado como una plantilla estructurada de ReAct. Su toma de decisiones demuestra la combinación de tres coordenadas de información que los asistentes del taller pueden expandir:

1.  **Herramientas Locales a Medida (`generic_tool`):** Una función local estructurada que sirve de placeholder para que los alumnos aprendan a programar y exponer lógicas personalizadas de Python al modelo.
2.  **Servidor MCP Remoto (`generic_mcp_tool`):** Llama a un microservicio externo compatible con el estándar abierto **Model Context Protocol (MCP)** para realizar consultas estructuradas de base de datos o APIs remotas de forma segura.
3.  **Colaboración Remota vía A2A (`partner_agent`):** Utiliza la interconexión nativa de A2A de Google ADK para comunicarse de manera remota con otros agentes del ecosistema que exponen habilidades y delegar tareas especializadas de forma transparente.

---

## 📁 Estructura del Proyecto y Carpetas

A continuación se detalla qué contiene cada carpeta del proyecto y para qué sirve en el desarrollo de tu agente:

### 1. `app/` (Código Principal del Agente)
Esta es la carpeta más importante, donde residirá toda la lógica de inteligencia de tu agente:
*   `agent.py`: El punto de entrada principal. Aquí se definen las instrucciones de comportamiento (prompt del sistema), se registran los callbacks de observabilidad, se cargan los esquemas A2A y se instancian las herramientas del agente. **Contiene secciones de ejercicio (`TODO: [EJERCICIO]`) listas para que las programes.**
*   `agent_runtime_app.py`: Archivo estándar que actúa como envoltorio (wrapper) de FastAPI. Es necesario para empaquetar tu agente y permitir que se ejecute en **Agent Runtime (Reasoning Engines)** en Google Cloud de forma serverless.
*   `partner_agent_card.json`: Fichero de manifiesto (Agent Card) en formato JSON. Describe las capacidades y los endpoints de conexión de un agente externo con el que tu agente puede hablar de forma nativa a través de A2A.
*   `app_utils/`: Carpeta de soporte generada por la ADK para manejar tipos de datos y la telemetría automática. No requiere modificación.

### 2. `skills/` (Directorio de Habilidades Dinámicas)
*   Contiene manuales e instrucciones expertas escritas en Markdown (ej: `weather_report_skill.md`).
*   **¿Para qué sirve?** El agente lee dinámicamente estos archivos (vía GCS o disco local) en caliente durante la inicialización del chat y los inyecta en su prompt. Esto permite actualizar o añadir nuevas destrezas al agente en tiempo real sin tener que redesplegar una sola línea de código en producción.

### 3. `mcp-server/` (Servidor MCP de Ejemplo)
*   Implementa un servidor de **Model Context Protocol (MCP)** desarrollado en **Node.js** que se comunica vía entrada/salida estándar (stdio) o HTTP/SSE utilizando JSON-RPC 2.0.
*   **¿Para qué sirve?** Sirve como una plantilla de referencia real de cómo desarrollar, estructurar y exponer herramientas y recursos a través del estándar MCP de manera privada en Cloud Run.

### 4. `deployment/` (Infraestructura de Despliegue)
*   Contiene configuraciones de **Terraform** listas para producción.
*   **¿Para qué sirve?** Facilita el aprovisionamiento automatizado e idéntico de toda la infraestructura que requiere tu agente en Google Cloud (buckets de GCS para reportes y habilidades, políticas de IAM, conectores de red y el propio servicio de ejecución del agente).

### 5. Archivos en la Raíz del Proyecto
*   `setup.sh`: Script en castellano que prepara todo tu entorno de desarrollo en un solo paso (instalación de `uv`, `google-agents-cli`, dependencias del proyecto y login en GCP).
*   `pyproject.toml` y `uv.lock`: Definen los requisitos del sistema y las dependencias de Python administradas de forma ultra rápida por `uv`.

---

## 🛠️ Comandos Útiles del Proyecto

Una vez ejecutado el `./setup.sh`, puedes interactuar con tu entorno virtual mediante los siguientes comandos:

| Comando | Descripción |
| :--- | :--- |
| `source .venv/bin/activate` | Activa el entorno virtual de Python en tu terminal. |
| `uv run adk run app` | **Inicia tu agente en modo consola interactiva** (puedes chatear con él directamente en la terminal). |
| `uv run adk web --port 8080 .` | Lanza el Web UI interactivo (Playground visual) de la ADK en el puerto `8080`. |
| `agents-cli deploy` | Empaqueta y despliega tu agente en **Agent Runtime** de Google Cloud. |
| `agents-cli publish gemini-enterprise` | Registra el agente en la consola de **Gemini Enterprise** para que tu equipo pueda usarlo. |

---

## 📡 Modo Offline / Local-First (Desarrollo Rápido)

Este boilerplate está preparado para ejecutarse en modo **Local-First**, permitiéndote probar todo el flujo de comportamiento de manera local y offline, sin necesidad de conectarse a internet o configurar credenciales de Google Cloud inicialmente.

Para activarlo, asegúrate de tener configurado en tu archivo `.env` local:
```env
OFFLINE_MODE=true
```
Esto redirigirá la descarga de habilidades al disco local, simulará consultas locales de tu servidor MCP y mantendrá la ejecución libre de conexiones de red externas obligatorias.
