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
from app.agent import read_production_schedule, remote_logistics_agent, save_markdown_report, get_port_weather


def test_read_production_schedule() -> None:
    """Tests that read_production_schedule can locate and read the production schedule JSON."""
    result = read_production_schedule()
    assert result["status"] == "success"
    assert "containers" in result
    assert len(result["containers"]) > 0
    
    # Check that a known container exists in the list
    container_ids = [c["container_id"] for c in result["containers"]]
    assert "CMDU4651065" in container_ids


def test_remote_logistics_agent_initialization() -> None:
    """Tests that the RemoteA2aAgent is initialized correctly with its Agent Card."""
    assert remote_logistics_agent.name == "logistics_agent"
    assert "Agente remoto de logística" in remote_logistics_agent.description
    
    # Check that the agent card JSON was loaded correctly
    card_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "app", "logistics_agent_card.json")
    )
    assert os.path.exists(card_path)


def test_save_markdown_report() -> None:
    """Tests that the generic file-writer save_markdown_report correctly persists reports in reports/."""
    test_filename = "test_climate_report.md"
    test_content = "# Test Climate Report\n\nThis is a sample test report."
    
    result = save_markdown_report(test_filename, test_content)
    assert result["status"] == "success"
    assert "test_climate_report.md" in result["filename"]
    assert os.path.exists(result["filepath"])
    
    # Verify contents written are identical
    with open(result["filepath"], "r", encoding="utf-8") as f:
        written_content = f.read()
    assert written_content == test_content
    
    # Cleanup test file
    try:
        os.remove(result["filepath"])
    except Exception:
        pass


def test_get_port_weather_live() -> None:
    """Tests that the get_port_weather tool securely connects to the deployed Cloud Run MCP and fetches live results."""
    # Test with Bilbao
    result = get_port_weather("Bilbao, ES")
    assert "Bilbao" in result
    assert "Transport risk" in result
    
    # Test with Buenos Aires
    result_ba = get_port_weather("Buenos Aires, AR")
    assert "Buenos Aires" in result_ba
    assert "Transport risk" in result_ba
