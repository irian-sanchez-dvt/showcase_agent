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
import requests
import google.auth
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from a2a.types import AgentCard

# Load local environment variables from .env file if present
possible_env_paths = [
    ".env",
    "../.env",
    os.path.join(os.path.dirname(__file__), "..", ".env"),
]
for env_path in possible_env_paths:
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip()
            break
        except Exception:
            pass

# Set up GCP and Vertex AI environment variables
_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT", project_id)
os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west1")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("factory-planner")

# Detect OFFLINE_MODE
IS_OFFLINE = os.getenv("OFFLINE_MODE", "false").lower() == "true"
if IS_OFFLINE:
    logger.info("📡 [MODO OFFLINE ACTIVADO] El agente se ejecutará en modo Local-First sin conectar a GCP.")

# ---------------------------------------------------------------------------
# 0. DINAMIC LOCAL & REMOTE SKILL LOADER
# ---------------------------------------------------------------------------
def load_local_skills() -> str:
    """Escanea la carpeta local de skills/ y lee todas las guías de habilidades en Markdown."""
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
        logger.warning("No se encontró la carpeta local 'skills/' para cargar habilidades.")
        return ""
        
    skills_content = []
    try:
        for filename in os.listdir(skills_dir):
            if filename.endswith(".md"):
                filepath = os.path.join(skills_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    skills_content.append(
                        f"\n\n--- HABILIDAD ADQUIRIDA (FALLBACK LOCAL): {filename} ---\n{content}\n"
                    )
        logger.info(f"Cargadas con éxito {len(skills_content)} habilidades locales.")
    except Exception as e:
        logger.error(f"Fallo al cargar habilidades locales de fallback: {str(e)}")
        
    if skills_content:
        return "\n\n=== MANUAL DE HABILIDADES ADQUIRIDAS (SISTEMA DE SKILLS LOCAL) ===\n" + "".join(skills_content)
    return ""


def load_gcs_skills() -> str:
    """Escanea el bucket de GCS y descarga todos los archivos .md

    de habilidades para inyectarlos dinámicamente en el prompt del sistema.
    Bypassa GCS si OFFLINE_MODE está activo.
    """
    if IS_OFFLINE:
        logger.info("Bypasseando descarga de GCS (Modo Offline). Cargando habilidades locales...")
        return load_local_skills()

    try:
        from google.cloud import storage
        bucket_name = os.getenv("GCS_SKILLS_BUCKET", "dvt-sp-agentspace-factory-skills")
        skills_content = []
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blobs = list(bucket.list_blobs())
        
        count = 0
        for blob in blobs:
            if blob.name.endswith(".md") and not "/" in blob.name:  # Evita descargar reportes guardados
                content = blob.download_as_text(encoding="utf-8")
                skills_content.append(
                    f"\n\n--- HABILIDAD ADQUIRIDA (DESDE GCS): {blob.name} ---\n{content}\n"
                )
                count += 1
                
        logger.info(f"Cargadas con éxito {count} habilidades remota(s) desde el bucket GCS '{bucket_name}'.")
    except Exception as e:
        logger.error(f"Fallo al cargar habilidades dinámicas desde GCS: {str(e)}. Activando fallback local offline.")
        return load_local_skills()
        
    if skills_content:
        return "\n\n=== MANUAL DE HABILIDADES ADQUIRIDAS (SISTEMA DE SKILLS GCS) ===\n" + "".join(skills_content)
    return ""


def load_gcs_config() -> dict:
    """Descarga de forma segura el archivo 'config.json' desde GCS para recuperar

    las variables de entorno de producción. Bypassa GCS si OFFLINE_MODE está activo.
    """
    if IS_OFFLINE:
        return {}

    bucket_name = os.getenv("GCS_SKILLS_BUCKET", "dvt-sp-agentspace-factory-skills")
    blob_name = "config.json"
    
    try:
        from google.cloud import storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        if blob.exists():
            data_text = blob.download_as_text(encoding="utf-8")
            logger.info("Configuración remota descargada con éxito desde Google Cloud Storage (GCS).")
            return json.loads(data_text)
    except Exception as e:
        logger.warning(f"No se pudo descargar la configuración remota desde GCS: {e}")
    return {}


# ---------------------------------------------------------------------------
# 1. LOCAL & REMOTE FLEET SCHEDULE SKILL (read_production_schedule)
# ---------------------------------------------------------------------------
def read_production_schedule() -> dict:
    """Consulta la flota activa de contenedores y sus cronogramas de arribo.

    En modo online lee de GCS; en modo offline de forma inmediata lee del disco local.

    Returns:
        dict: Un diccionario JSON con el estado de la operación y el listado de contenedores en la flota.
    """
    if not IS_OFFLINE:
        bucket_name = os.getenv("GCS_SKILLS_BUCKET", "dvt-sp-agentspace-factory-skills")
        blob_name = "production_schedule.json"
        
        # Intento de cargar dinámicamente desde GCS en la nube
        try:
            from google.cloud import storage
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            if blob.exists():
                data_text = blob.download_as_text(encoding="utf-8")
                return {"status": "success", "containers": json.loads(data_text), "source": "GCS"}
        except Exception as e:
            logger.error(f"Fallo al leer archivo de cronograma en GCS: {str(e)}")
        
    # Fallback local / Modo Offline directo
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
                    logger.info("Cronograma de producción leído del disco local (Modo Local/Fallback).")
                    return {"status": "success", "containers": data, "source": "local"}
            except Exception:
                pass
                
    return {"status": "error", "message": "No se pudo encontrar el archivo de cronograma en GCS ni en local."}


# ---------------------------------------------------------------------------
# 2. REMOTE LOGISTICS A2A AGENT INTEGRATION (Agent-to-Agent Skill)
# ---------------------------------------------------------------------------
# Resolve the path to our local high-fidelity agent card
agent_card_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "logistics_agent_card.json")
)

# Load the JSON and override the connection URL dynamically from environment
with open(agent_card_path, "r", encoding="utf-8") as f:
    card_data = json.load(f)

# Override with private logistics URL from .env securely if available locally
env_url = os.getenv("LOGISTICS_AGENT_URL")
if env_url:
    card_data["url"] = env_url
    logger.info("URL de conexión del agente de logística cargada de forma segura desde .env local.")

# Instantiate the RemoteA2aAgent using Google ADK native A2A support
remote_logistics_agent = RemoteA2aAgent(
    name="logistics_agent",
    agent_card=AgentCard(**card_data), # Pass instantiated AgentCard object directly
    description="Agente remoto de logística marítima capaz de rastrear contenedores específicos por ID (track_by_id) y realizar consultas complejas sobre la flota, rutas y retrasos en BigQuery (query_logistics).",
)


# ---------------------------------------------------------------------------
# 3. WEATHER MCP SERVER INTEGRATION (get_port_weather)
# ---------------------------------------------------------------------------
import subprocess

def get_google_id_token(audience: str) -> str:
    """Genera un token de identidad OIDC de Google para autenticarse en Cloud Run.

    Usa la Service Account en la nube (Vertex AI) y gcloud como fallback local para desarrollo.
    """
    # 1. Intento Cloud (Service Account / Metadata Server en Vertex AI)
    try:
        import google.oauth2.id_token
        from google.auth.transport.requests import Request
        auth_req = Request()
        token = google.oauth2.id_token.fetch_id_token(auth_req, audience)
        return token
    except Exception:
        # 2. Fallback Local para Desarrollo (gcloud auth print-identity-token)
        try:
            result = subprocess.run(
                ["gcloud", "auth", "print-identity-token"],
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception as local_err:
            logger.warning(f"No se pudo generar el ID Token localmente para el MCP: {local_err}")
            return ""

def get_port_weather(port: str) -> str:
    """Checks the actual real-time weather at a specific port of origin using global weather APIs to assess meteorological hazards for maritime transport.

    Args:
        port: The port city and country name (e.g., Bilbao, ES, Buenos Aires, AR, Vancouver, CA).

    Returns:
        str: El reporte meteorológico detallado en castellano y el nivel de riesgo de transporte terrestre/marítimo.
    """
    fallback_offline_data = {
      "buenos aires, ar": { "weather": "Sunny, calm seas.", "risk": "LOW" },
      "bilbao, es": { "weather": "Severe storm, gale-force winds, heavy swells.", "risk": "HIGH" },
      "felixstowe, uk": { "weather": "Dense fog, restricted visibility.", "risk": "MEDIUM" },
      "jeddah, sa": { "weather": "Sunny, high temperatures, calm seas.", "risk": "LOW" },
      "busan, kr": { "weather": "Partly cloudy, light breeze.", "risk": "LOW" },
      "noumea, nc": { "weather": "Tropical depression nearby, rough seas, windy.", "risk": "MEDIUM" },
      "callao, pe": { "weather": "Clear sky, moderate currents.", "risk": "LOW" },
      "tangier, ma": { "weather": "Clear, mild winds.", "risk": "LOW" },
      "vancouver, ca": { "weather": "Heavy rainfall and strong offshore winds.", "risk": "HIGH" }
    }

    # 1. Si OFFLINE_MODE es true, consultamos de forma 100% local sin red
    if IS_OFFLINE:
        logger.info("📡 [MODO OFFLINE] Resolviendo el clima del puerto localmente...")
        # Intento de llamar a un servidor Node local ejecutándose en el puerto 3000
        try:
            response = requests.post("http://localhost:3000/get_port_weather", json={"port": port}, timeout=2)
            if response.status_code == 200:
                return response.json().get("text", "No se pudo recuperar el reporte local.")
        except Exception:
            pass
            
        # Fallback instantáneo en Python puro si no hay servidor local corriendo (Demo Blindada)
        clean_key = port.lower().strip()
        matched_info = { "weather": "Partly cloudy, calm seas.", "risk": "LOW" }
        for k, val in fallback_offline_data.items():
            if k in clean_key or clean_key in k:
                matched_info = val
                break
        return f"Port Location: {port}. [OFFLINE MOCK DATA] {matched_info['weather']} Transport risk evaluation is: {matched_info['risk']}."

    # 2. Modo Producción Remoto en la Nube (Cloud Run)
    mcp_audience = "https://weather-mcp-server-239233954615.europe-west1.run.app"
    mcp_url = f"{mcp_audience}/get_port_weather"
    
    # Obtener el token de identidad para pasar la seguridad IAM de Cloud Run de forma segura
    id_token = get_google_id_token(mcp_audience)
    headers = {"Content-Type": "application/json"}
    if id_token:
        headers["Authorization"] = f"Bearer {id_token}"
        
    try:
        response = requests.post(mcp_url, json={"port": port}, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("text", "No se pudo recuperar el reporte de clima.")
        else:
            return f"Error al conectar con el microservicio de clima (HTTP {response.status_code}): {response.text}"
    except Exception as e:
        return f"Error de red al conectar con el microservicio de clima en Cloud Run: {str(e)}"


# ---------------------------------------------------------------------------
# 4. REMOTE GCS DISK INFRASTRUCTURE TOOL (save_markdown_report)
# ---------------------------------------------------------------------------
def save_markdown_report(filename: str, content: str) -> dict:
    """Guarda un reporte o archivo de texto formateado en el disco local y lo sube de forma pública a Google Cloud Storage.

    Args:
        filename: El nombre del archivo a crear o guardar (ej: 'reporte_clima_bilbao.md').
        content: El contenido de texto completo formateado en Markdown que se escribirá en el archivo.

    Returns:
        dict: El estado de la operación, la ruta del archivo local y el enlace de descarga en GCS.
    """
    clean_name = os.path.basename(filename)
    
    # 1. Guardado Local (Consistencia y Testing)
    try:
        reports_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "reports")
        )
        os.makedirs(reports_dir, exist_ok=True)
        
        filepath = os.path.join(reports_dir, clean_name)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        logger.warning(f"No se pudo guardar localmente el reporte: {e}")
        filepath = "local_save_failed"

    # 2. Si estamos en modo offline, omitimos subir a GCS y retornamos de inmediato éxito local
    if IS_OFFLINE:
        logger.info("📡 [MODO OFFLINE] Reporte climático guardado localmente con éxito.")
        return {
            "status": "success",
            "message": "Reporte climático guardado con éxito en disco local.",
            "filepath": filepath,
            "filename": clean_name,
            "download_url": "No disponible (Modo Local/Offline)"
        }

    # 3. Subida a Google Cloud Storage con Generación de Enlace de Descarga (Producción)
    try:
        from google.cloud import storage
        bucket_name = os.getenv("GCS_SKILLS_BUCKET", "dvt-sp-agentspace-factory-skills")
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        
        # Subimos el archivo a la carpeta reports/ del bucket
        gcs_blob_path = f"reports/{clean_name}"
        blob = bucket.blob(gcs_blob_path)
        
        # Configuramos el tipo de contenido Markdown y codificación UTF-8 para que el navegador lo muestre bien
        blob.upload_from_string(content, content_type="text/markdown; charset=utf-8")
        
        # Generamos la URL de descarga directa de GCS
        public_url = f"https://storage.googleapis.com/{bucket_name}/{gcs_blob_path}"
        logger.info(f"Reporte climático subido exitosamente a GCS: {public_url}")
        
        return {
            "status": "success",
            "message": "Reporte climático guardado exitosamente en Google Cloud Storage.",
            "filepath": filepath,
            "filename": clean_name,
            "download_url": public_url
        }
    except Exception as e:
        logger.error(f"Fallo al guardar el reporte en GCS: {str(e)}")
        return {
            "status": "success",  # Retornamos success local si falla GCS para ser resilientes en desarrollo local offline
            "message": "Reporte climático guardado en disco local (GCS no disponible).",
            "filepath": filepath,
            "filename": clean_name,
            "download_url": "No disponible (Offline)"
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
        
    # Cargar las skills de GCS (u offline) de forma diferida (lazy loading) dentro del event loop activo
    # para evitar el error anyio.NoEventLoopError durante el import/inicialización del módulo
    if not hasattr(root_agent, "_gcs_skills_loaded"):
        logger.info("Iniciando la carga diferida (lazy loading) de habilidades...")
        dynamic_skills = load_gcs_skills()
        root_agent.instruction = base_instruction + dynamic_skills
        root_agent._gcs_skills_loaded = True
        logger.info("Habilidades cargadas con éxito e inyectadas en las instrucciones del agente.")
        
    # Cargar y sobrescribir la configuración remota desde GCS en caliente para recuperar
    # la URL real del agente de logística (OIDC/A2A) sin depender de variables .env locales en la nube
    try:
        gcs_config = load_gcs_config()
        logistics_url = gcs_config.get("LOGISTICS_AGENT_URL") or os.getenv("LOGISTICS_AGENT_URL")
        if logistics_url:
            remote_logistics_agent._agent_card.url = logistics_url
            logger.info(f"URL de conexión A2A de logística inyectada con éxito: {logistics_url}")
    except Exception as e:
        logger.error(f"Fallo al inyectar la URL dinámica de logística: {e}")
        
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
1. Utiliza la herramienta `read_production_schedule` para buscar el contenedor solicitado en el cronograma local de Google Cloud Storage.
2. **Lógica de Búsqueda de Contenedor:**
   - **Si encuentras el contenedor en el cronograma local:** identifica su puerto de origen (o 'pol'). Luego, consulta el clima de dicho puerto utilizando la herramienta `get_port_weather` para evaluar riesgos de transporte. También debes llamar a la herramienta `logistics_agent` (pasando el ID en el parámetro `request`, ej: `logistics_agent(request="CMDU4651065")`) para obtener su contenido y estado de aduanas.
   - **Si NO encuentras el contenedor en el cronograma local:** no te detengas. Llama de inmediato a la herramienta `logistics_agent` pasando el ID del contenedor como argumento del parámetro `request` (ej: `logistics_agent(request="CMDU4651065")` o `logistics_agent(request="Rastrea el ID CMDU4651065")`) para que el agente remoto busque el contenedor en su base de datos global. Si el agente remoto responde con los detalles y el puerto de origen (pol), consulta el clima de ese puerto con la herramienta `get_port_weather`.
3. Genera una recomendación final muy detallada en español sobre si el lote de producción puede iniciarse o si debe ser demorado, basándote exactamente en la información recolectada de las herramientas anteriores. Justifica tu decisión con los datos obtenidos.

**Regla de Seguridad Crítica:**
No inventes datos bajo ninguna circunstancia. Si el contenedor no está en el cronograma local ni el agente de logística tiene registro de él (es decir, la herramienta `logistics_agent` no devuelve datos válidos o indica que no existe), indica que no es posible iniciar el lote de producción por falta de información y detalla qué herramientas consultaste.
"""

root_agent = Agent(
    name="factory_planner",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description="Planificador de fábrica experto que valida si un lote de producción puede iniciarse. Cruza datos de cronogramas locales de flota, clima real de puertos, y consulta detalles de carga vía protocolo A2A.",
    instruction=base_instruction, # Arranca con la instrucción base; las skills se inyectan dinámicamente en init_session_state
    tools=[
        read_production_schedule,
        AgentTool(remote_logistics_agent),
        get_port_weather,  # Herramienta climática remota que se comunica de forma autenticada con el microservicio MCP en Cloud Run
        save_markdown_report,  # Herramienta de GCS que guarda el reporte localmente y lo sube con URL pública de descarga a Google Cloud Storage
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
