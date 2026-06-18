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

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from app.agent import root_agent

def run_local_simulation():
    print("+--------------------------------------------------+")
    print("| 🧪 INICIANDO SIMULACIÓN LOCAL DEL PLANIFICADOR    |")
    print("+--------------------------------------------------+")
    
    # 1. Inicializar sesión ADK 2.x
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    # 2. Formular consulta
    query = "Valida si el contenedor CMDU4651065 está listo para que iniciemos el lote de producción y, usando tu habilidad de GCS, genérame su reporte de clima en Markdown."
    print(f"\n👉 Consulta: '{query}'\n")
    
    message = types.Content(
        role="user", parts=[types.Part.from_text(text=query)]
    )

    print("Enviando consulta al agente...")
    events = runner.run(
        new_message=message,
        user_id="test_user",
        session_id=session.id,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE),
    )

    for event in events:
        if hasattr(event, "text") and event.text:
            print(event.text, end="", flush=True)
            
    print("\n\n+--------------------------------------------------+")
    print("| 🧪 PRUEBA LOCAL COMPLETADA CON ÉXITO             |")
    print("+--------------------------------------------------+")

if __name__ == "__main__":
    run_local_simulation()
