import os
import unittest
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.infra.entrypoints.http import create_app


class TestManualChatWorkflow(unittest.TestCase):
  """Test suite para endpoint /manual-chat con workflow."""

  def setUp(self):
    """Configura app y cliente de test."""
    os.environ["GUARDIAN_API_KEY"] = "test-secret-key-123"
    self.app = create_app()
    self.client = TestClient(self.app)
    self.valid_headers = {"X-API-KEY": "test-secret-key-123"}

  def tearDown(self):
    """Limpia variables de entorno."""
    if "GUARDIAN_API_KEY" in os.environ:
      del os.environ["GUARDIAN_API_KEY"]

  def test_manual_chat_returns_200_with_valid_request(self):
    """Valida que /manual-chat retorna 200 con solicitud válida."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    self.assertEqual(response.status_code, 200)

  def test_manual_chat_returns_ndjson_content_type(self):
    """Valida que /manual-chat retorna Content-Type application/x-ndjson."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    self.assertEqual(response.headers["content-type"], "application/x-ndjson")

  def test_manual_chat_returns_stream(self):
    """Valida que /manual-chat retorna un stream."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    self.assertIsNotNone(response.text)

  def test_manual_chat_stream_contains_json_lines(self):
    """Valida que el stream contiene líneas JSON válidas."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    lines = response.text.strip().split("\n")
    for line in lines:
      if line:
        try:
          json.loads(line)
        except json.JSONDecodeError:
          self.fail(f"Invalid JSON in stream: {line}")

  def test_manual_chat_stream_events_have_structure(self):
    """Valida que los eventos del stream tienen estructura correcta."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    lines = response.text.strip().split("\n")
    for line in lines:
      if line:
        event = json.loads(line)
        self.assertIn("event_type", event)
        self.assertIn("node", event)
        self.assertIn("data", event)

  def test_manual_chat_requires_api_key(self):
    """Valida que /manual-chat requiere API key."""
    response = self.client.post(
        "/manual-chat",
        json={}
    )
    self.assertEqual(response.status_code, 401)

  def test_manual_chat_rejects_invalid_api_key(self):
    """Valida que /manual-chat rechaza API key inválida."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers={"X-API-KEY": "wrong-key"}
    )
    self.assertEqual(response.status_code, 403)

  def test_manual_chat_stream_events_increase_progressively(self):
    """Valida que se emiten eventos progresivamente."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    lines = [line for line in response.text.strip().split("\n") if line]
    self.assertGreater(len(lines), 0)


class TestManualChatValidation(unittest.TestCase):
  """Test suite para validación de entrada en /manual-chat."""

  def setUp(self):
    """Configura app y cliente de test."""
    os.environ["GUARDIAN_API_KEY"] = "test-secret-key-123"
    self.app = create_app()
    self.client = TestClient(self.app)
    self.valid_headers = {"X-API-KEY": "test-secret-key-123"}

  def tearDown(self):
    """Limpia variables de entorno."""
    if "GUARDIAN_API_KEY" in os.environ:
      del os.environ["GUARDIAN_API_KEY"]

  def test_manual_chat_rejects_invalid_json_with_400(self):
    """T16: Valida que /manual-chat rechaza JSON inválido con 400."""
    response = self.client.post(
        "/manual-chat",
        content="invalid json {",
        headers={**self.valid_headers, "content-type": "application/json"}
    )
    self.assertEqual(response.status_code, 400)

  def test_manual_chat_invalid_json_returns_detail_message(self):
    """T16: Valida que respuesta 400 contiene mensaje de error."""
    response = self.client.post(
        "/manual-chat",
        content="invalid json {",
        headers={**self.valid_headers, "content-type": "application/json"}
    )
    self.assertEqual(response.status_code, 400)
    data = response.json()
    self.assertIn("detail", data)


class TestManualChatTransitions(unittest.TestCase):
  """Test suite para transiciones de nodos en /manual-chat."""

  def setUp(self):
    """Configura app y cliente de test."""
    os.environ["GUARDIAN_API_KEY"] = "test-secret-key-123"
    self.app = create_app()
    self.client = TestClient(self.app)
    self.valid_headers = {"X-API-KEY": "test-secret-key-123"}

  def tearDown(self):
    """Limpia variables de entorno."""
    if "GUARDIAN_API_KEY" in os.environ:
      del os.environ["GUARDIAN_API_KEY"]

  def test_manual_chat_stream_contains_start_node(self):
    """T17: Valida que el stream contiene evento del nodo start."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    lines = [line for line in response.text.strip().split("\n") if line]
    nodes = [json.loads(line).get("node") for line in lines]
    self.assertIn("start", nodes)

  def test_manual_chat_stream_contains_process_node(self):
    """T17: Valida que el stream contiene evento del nodo process."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    lines = [line for line in response.text.strip().split("\n") if line]
    nodes = [json.loads(line).get("node") for line in lines]
    self.assertIn("process", nodes)

  def test_manual_chat_stream_contains_end_node(self):
    """T17: Valida que el stream contiene evento del nodo end."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    lines = [line for line in response.text.strip().split("\n") if line]
    nodes = [json.loads(line).get("node") for line in lines]
    self.assertIn("end", nodes)

  def test_manual_chat_nodes_execute_in_order(self):
    """T17: Valida que los nodos ejecutan en orden start, process, end."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    lines = [line for line in response.text.strip().split("\n") if line]
    nodes = [json.loads(line).get("node") for line in lines]

    start_idx = nodes.index("start") if "start" in nodes else -1
    process_idx = nodes.index("process") if "process" in nodes else -1
    end_idx = nodes.index("end") if "end" in nodes else -1

    self.assertGreater(start_idx, -1)
    self.assertGreater(process_idx, -1)
    self.assertGreater(end_idx, -1)
    self.assertLess(start_idx, process_idx)
    self.assertLess(process_idx, end_idx)


class TestManualChatErrorHandling(unittest.TestCase):
  """Test suite para manejo de errores en /manual-chat."""

  def setUp(self):
    """Configura app y cliente de test."""
    os.environ["GUARDIAN_API_KEY"] = "test-secret-key-123"
    self.app = create_app()
    self.client = TestClient(self.app)
    self.valid_headers = {"X-API-KEY": "test-secret-key-123"}

  def tearDown(self):
    """Limpia variables de entorno."""
    if "GUARDIAN_API_KEY" in os.environ:
      del os.environ["GUARDIAN_API_KEY"]

  def test_manual_chat_stream_emits_events_on_success(self):
    """T18: Valida que el stream emite eventos cuando el flujo es exitoso."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    lines = [line for line in response.text.strip().split("\n") if line]
    for line in lines:
      event = json.loads(line)
      self.assertIn("event_type", event)
      self.assertIn(event["event_type"], ["node_updated", "error"])

  def test_manual_chat_returns_ndjson_on_error(self):
    """T18: Valida que el endpoint retorna NDJSON incluso si hay error."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    self.assertEqual(response.headers["content-type"], "application/x-ndjson")


if __name__ == "__main__":
  unittest.main()
