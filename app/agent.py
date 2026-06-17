# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import logging
import google.auth
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import McpToolset, AgentTool
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

# Set up GCP and Vertex AI environment variables
_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("factory-planner")

# ---------------------------------------------------------------------------
# 0. DINAMIC LOCAL SKILL LOADER
# ---------------------------------------------------------------------------
def load_local_skills() -> str:
    """Escanea la carpeta de skills/ y lee todas las guías de habilidades en Markdown

    para inyectarlas dinámicamente en el prompt del sistema al arrancar el agente.
    """
    possible_paths = [
        "skills",
        "../skills",
        os.path.join(os.path.dirname(__file__), "..", "skills"),
        os.path.join(os.path.dirname(__file__), "skills"),
    ]
    
    skills_dir = None
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            skills_dir = path
            break
            
    if not skills_dir:
        logger.warning("No se encontró la carpeta 'skills/' en las rutas preconfiguradas.")
        return ""
        
    skills_content = []
    try:
        for filename in os.listdir(skills_dir):
            if filename.endswith(".md"):
                filepath = os.path.join(skills_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    skills_content.append(
                        f"\n\n--- HABILIDAD ADQUIRIDA: {filename} ---\n{content}\n"
                    )
        logger.info(f"Cargadas con éxito {len(skills_content)} habilidades desde '{skills_dir}'.")
    except Exception as e:
        logger.error(f"Fallo al cargar habilidades dinámicas: {str(e)}")
        
    if skills_content:
        return "\n\n=== MANUAL DE HABILIDADES ADQUIRIDAS (SISTEMA DE SKILLS) ===\n" + "".join(skills_content)
    return ""


# ---------------------------------------------------------------------------
# 1. LOCAL FLEET SCHEDULE SKILL (read_production_schedule)
# ---------------------------------------------------------------------------
def read_production_schedule() -> dict:
    """Consulta la flota activa de contenedores y sus cronogramas de arribo.

    Esta habilidad busca en el archivo local 'production_schedule.json' (sincronizado con BigQuery)
    para identificar los contenedores actualmente en flota, sus transportistas (carriers),
    sus puertos de carga (pol) y descarga (pod), estimaciones de arribo (eta) y estados.

    Returns:
        dict: Un diccionario JSON con el estado de la operación y el listado de contenedores en la flota.
    """
    possible_paths = [
        "production_schedule.json",
        "../production_schedule.json",
        os.path.join(os.path.dirname(__file__), "..", "production_schedule.json"),
        os.path.join(os.path.dirname(__file__), "production_schedule.json"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {"status": "success", "containers": data}
            except Exception as e:
                return {"status": "error", "message": f"Fallo al leer archivo de cronograma: {str(e)}"}
                
    return {"status": "error", "message": "Archivo production_schedule.json no encontrado en el sistema local."}


# ---------------------------------------------------------------------------
# 2. REMOTE LOGISTICS A2A AGENT INTEGRATION (Agent-to-Agent Skill)
# ---------------------------------------------------------------------------
# Resolve the path to our local high-fidelity agent card
agent_card_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "logistics_agent_card.json")
)

# Instantiate the RemoteA2aAgent using Google ADK native A2A support
remote_logistics_agent = RemoteA2aAgent(
    name="logistics_agent",
    agent_card=agent_card_path,
    description="Agente remoto de logística marítima capaz de rastrear contenedores específicos por ID (track_by_id) y realizar consultas complejas sobre la flota, rutas y retrasos en BigQuery (query_logistics).",
)


# ---------------------------------------------------------------------------
# 3. WEATHER MCP SERVER TOOLSET (get_port_weather)
# ---------------------------------------------------------------------------
# Resolve the path to our real-time weather-server MCP index.js dynamically
mcp_server_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "weather-server", "index.js")
)

weather_mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="node",
            args=[mcp_server_path],
        ),
    ),
    # Restrict exposed tools to only expose get_port_weather
    tool_filter=["get_port_weather"],
)


# ---------------------------------------------------------------------------
# 4. GENERIC DISK INFRASTRUCTURE TOOL (save_markdown_report)
# ---------------------------------------------------------------------------
def save_markdown_report(filename: str, content: str) -> dict:
    """Guarda un reporte o archivo de texto formateado en el disco local dentro del directorio 'reports/'.

    Args:
        filename: El nombre del archivo a crear o guardar (ej: 'reports/reporte_clima_bilbao.md').
        content: El contenido de texto completo formateado en Markdown que se escribirá en el archivo.

    Returns:
        dict: El estado de la operación y la ruta absoluta del archivo guardado.
    """
    try:
        # Forzar guardado seguro en la carpeta reports/ para evitar path traversal
        clean_name = os.path.basename(filename)
        reports_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "reports")
        )
        os.makedirs(reports_dir, exist_ok=True)
        
        filepath = os.path.join(reports_dir, clean_name)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        return {
            "status": "success",
            "message": "Reporte climático guardado exitosamente en disco.",
            "filepath": filepath,
            "filename": clean_name
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Fallo al escribir el reporte en el disco: {str(e)}"
        }


# ---------------------------------------------------------------------------
# 5. CALLBACKS FOR OBSERVABILITY & SESSION STATE
# ---------------------------------------------------------------------------
async def init_session_state(callback_context: CallbackContext, **kwargs) -> None:
    """Callback triggered before agent execution to initialize and maintain session-level context."""
    if "validated_batches" not in callback_context.state:
        callback_context.state["validated_batches"] = []
    if "current_batch" not in callback_context.state:
        callback_context.state["current_batch"] = None
    logger.info(f"Session state initialized. Validated batches: {callback_context.state['validated_batches']}")


async def before_tool_call(tool, args: dict, tool_context, **kwargs) -> dict | None:
    """Callback triggered before executing any tool."""
    print(f"\n⚡ [ADK Tool Callback] CALLING tool: '{tool.name}' with args: {args}")
    return None


async def after_tool_call(tool, args: dict, tool_context, tool_response, **kwargs) -> dict | None:
    """Callback triggered after tool execution completes."""
    print(f"✅ [ADK Tool Callback] COMPLETED tool: '{tool.name}'. Result: {tool_response}\n")
    return None


# ---------------------------------------------------------------------------
# 6. AGENT DEFINITION
# ---------------------------------------------------------------------------
base_instruction = """Eres un planificador de fábrica experto. Tu misión es validar si un lote de producción puede iniciarse.

Para lograr esto, debes seguir este procedimiento paso a paso de forma rigurosa:
1. Utiliza la herramienta `read_production_schedule` para buscar el contenedor solicitado en el cronograma local.
2. **Lógica de Búsqueda de Contenedor:**
   - **Si encuentras el contenedor en el cronograma local:** identifica su puerto de origen (o 'pol'). Luego, consulta el clima de dicho puerto utilizando la herramienta MCP `get_port_weather` para evaluar riesgos de transporte. También debes llamar a la herramienta `logistics_agent` (pasando el ID en el parámetro `request`, ej: `logistics_agent(request="CMDU4651065")`) para obtener su contenido y estado de aduanas.
   - **Si NO encuentras el contenedor en el cronograma local:** no te detengas. Llama de inmediato a la herramienta `logistics_agent` pasando el ID del contenedor como argumento del parámetro `request` (ej: `logistics_agent(request="CMDU4651065")` o `logistics_agent(request="Rastrea el ID CMDU4651065")`) para que el agente remoto busque el contenedor en su base de datos global. Si el agente remoto responde con los detalles y el puerto de origen (pol), consulta el clima de ese puerto con la herramienta MCP `get_port_weather`.
3. Genera una recomendación final muy detallada en español sobre si el lote de producción puede iniciarse o si debe ser demorado, basándote exactamente en la información recolectada de las herramientas anteriores. Justifica tu decisión con los datos obtenidos.

**Regla de Seguridad Crítica:**
No inventes datos bajo ninguna circunstancia. Si el contenedor no está en el cronograma local ni el agente de logística tiene registro de él (es decir, la herramienta `logistics_agent` no devuelve datos válidos o indica que no existe), indica que no es posible iniciar el lote de producción por falta de información y detalla qué herramientas consultaste.
"""

# Load local skills dynamically from skills/ directory
dynamic_skills = load_local_skills()
final_instruction = base_instruction + dynamic_skills

root_agent = Agent(
    name="factory_planner",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description="Planificador de fábrica experto que valida si un lote de producción puede iniciarse. Cruza datos de cronogramas locales de flota, clima real de puertos mediante MCP, y consulta detalles de carga vía protocolo A2A.",
    instruction=final_instruction,
    tools=[
        read_production_schedule,
        AgentTool(remote_logistics_agent),
        weather_mcp_toolset,
        save_markdown_report,  # Herramienta de infraestructura genérica requerida por la habilidad climática para persistir los reportes Markdown en disco
    ],
    before_agent_callback=init_session_state,
    before_tool_callback=before_tool_call,
    after_tool_callback=after_tool_call,
)

# ---------------------------------------------------------------------------
# 7. APP DEFINITION (adkapp pattern)
# ---------------------------------------------------------------------------
app = App(
    root_agent=root_agent,
    name="app",
)
