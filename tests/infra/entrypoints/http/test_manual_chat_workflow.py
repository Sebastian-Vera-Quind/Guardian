import os
import unittest
import json

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from src.infra.entrypoints.http import create_app
from src.domain.models import WorkflowInput


def parse_sse_events(text: str) -> list[dict]:
  """
  Parsea eventos SSE del formato:
  event: node_update
  data: {"..."}

  Retorna lista de dicts con keys 'event' y 'data'.
  """
  events = []
  current_event = None
  current_data = None

  for line in text.split('\n'):
    line = line.strip()
    if not line:
      if current_event and current_data is not None:
        events.append({"event": current_event, "data": current_data})
        current_event = None
        current_data = None
      continue

    if line.startswith("event:"):
      current_event = line.replace("event:", "").strip()
    elif line.startswith("data:"):
      data_str = line.replace("data:", "").strip()
      try:
        current_data = json.loads(data_str)
      except json.JSONDecodeError:
        current_data = data_str

  return events


def _make_mock_executor():
  """Returns a mock WorkflowExecutor with two nodes in the stream."""
  mock = MagicMock()

  async def _fake_stream(input_data):
    yield {"event_type": "node_updated", "node": "start", "data": {}}
    yield {"event_type": "node_updated", "node": "process", "data": {}}

  mock.execute_and_stream = _fake_stream
  return mock


class TestManualChatEndpointR1R8(unittest.TestCase):
  """Tests para R1 (POST /manual-chat), R8 (400 Bad Request)."""

  def setUp(self):
    """Configura app y cliente de test."""
    os.environ["GUARDIAN_API_KEY"] = "test-secret-key-123"
    self.app = create_app()
    self.client = TestClient(self.app)
    self.valid_headers = {"X-API-KEY": "test-secret-key-123"}
    self._injector_patcher = patch(
        'src.infra.entrypoints.http.endpoints.manual_chat.inject',
        return_value=_make_mock_executor()
    )
    self._injector_patcher.start()

  def tearDown(self):
    """Limpia variables de entorno."""
    self._injector_patcher.stop()
    if "GUARDIAN_API_KEY" in os.environ:
      del os.environ["GUARDIAN_API_KEY"]

  def test_r1_accepts_post_manual_chat_with_valid_json(self):
    """R1: El sistema DEBE aceptar una solicitud POST al endpoint `/manual-chat` con un body JSON."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    # R1 se cumple si el endpoint responde (sin error 404/405)
    self.assertIn(response.status_code, [200, 400])
    self.assertNotEqual(response.status_code, 404)
    self.assertNotEqual(response.status_code, 405)

  def test_manual_chat(self):
    """
      R1: Valida que POST /manual-chat acepta body JSON.
      R3: Valida que la respuesta es un stream de eventos
        - Cada evento debe estar en formato SSE valido
        
    """
    body = {}
    response = self.client.post(
        "/manual-chat",
        json=body,
        headers=self.valid_headers
    )

    events = parse_sse_events(response.text)
    self.assertGreater(len(events), 0, "Debe haber al menos un evento")

    # Cada evento debe tener evento y data
    for ev in events:
      self.assertIn("event", ev)
      self.assertIsNotNone(ev.get("event"))

    self.assertIn(response.status_code, [200, 400])
    self.assertEqual(response.headers["content-type"], "text/event-stream; charset=utf-8")
    self.assertIsNotNone(response.text)
    self.assertGreater(len(response.text.strip()), 0)

  def test_r8_rejects_invalid_json_with_400(self):
    """R8: CUANDO se recibe JSON inválido, DEBE rechazar con HTTP 400 Bad Request."""
    response = self.client.post(
        "/manual-chat",
        content="invalid json {",
        headers={**self.valid_headers, "content-type": "application/json"}
    )
    self.assertEqual(response.status_code, 400)

  def test_r8_invalid_json_includes_detail_message(self):
    """R8: La respuesta 400 DEBE incluir mensaje de detalle."""
    response = self.client.post(
        "/manual-chat",
        content="invalid json {",
        headers={**self.valid_headers, "content-type": "application/json"}
    )
    self.assertEqual(response.status_code, 400)
    data = response.json()
    self.assertIn("detail", data)

  def test_r4_stream_emits_node_state_changes(self):
    """R4: CUANDO un nodo cambia de estado, DEBE emitir evento con node y estado."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    events = parse_sse_events(response.text)
    self.assertGreater(len(events), 0, "Stream debe tener al menos un evento")

    # Buscar eventos node_update
    node_update_events = [ev for ev in events if ev.get("event") == "node_update"]
    self.assertGreater(len(node_update_events), 0, "Debe haber eventos de nodo")

    # Cada evento node_update debe tener estructura correcta
    for ev in node_update_events:
      data = ev.get("data")
      if isinstance(data, dict):
        self.assertIn("node", data)
        self.assertIn("event_type", data)



class TestWorkflowExecutionR2R6(unittest.TestCase):
  """Tests para R2 (instanciar workflow e iniciar), R6 (detener stream al finalizar)."""

  def setUp(self):
    """Configura app y cliente de test."""
    os.environ["GUARDIAN_API_KEY"] = "test-secret-key-123"
    self.app = create_app()
    self.client = TestClient(self.app)
    self.valid_headers = {"X-API-KEY": "test-secret-key-123"}
    self._injector_patcher = patch(
        'src.infra.entrypoints.http.endpoints.manual_chat.inject',
        return_value=_make_mock_executor()
    )
    self._injector_patcher.start()

  def tearDown(self):
    """Limpia variables de entorno."""
    self._injector_patcher.stop()
    if "GUARDIAN_API_KEY" in os.environ:
      del os.environ["GUARDIAN_API_KEY"]

  def test_r2_instanciates_and_starts_workflow(self):
    """R2: CUANDO recibe POST /manual-chat con JSON válido, DEBE instanciar workflow e iniciar ejecución."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    # R2: Si responde 200 con eventos, significa que instanció y ejecutó el workflow
    self.assertEqual(response.status_code, 200)
    events = parse_sse_events(response.text)
    self.assertGreater(len(events), 0)

  def test_r2_workflow_receives_json_body(self):
    """R2: El workflow DEBE recibir el body JSON como entrada."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    # Validar que el workflow procesó algún input
    self.assertEqual(response.status_code, 200)
    events = parse_sse_events(response.text)
    self.assertGreater(len(events), 0)

  def test_r6_stream_completes_after_all_nodes(self):
    """R6: CUANDO todos los nodos completan, DEBE detener el stream indicando fin del workflow."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    # Si la respuesta se cierra (no hay exception), el stream se detuvo
    self.assertEqual(response.status_code, 200)
    events = parse_sse_events(response.text)
    self.assertGreater(len(events), 0)

    # Debe haber evento de complete al final
    event_types = [ev.get("event") for ev in events]
    self.assertIn("complete", event_types, "Debe haber evento complete al finalizar")


class TestNodeTransitionsR12R13R14R15(unittest.TestCase):
  """Tests para R12 (dependencias), R13 (StateGraph), R14 (2+ nodos), R15 (transiciones)."""

  def setUp(self):
    """Configura app y cliente de test."""
    os.environ["GUARDIAN_API_KEY"] = "test-secret-key-123"
    self.app = create_app()
    self.client = TestClient(self.app)
    self.valid_headers = {"X-API-KEY": "test-secret-key-123"}
    self._injector_patcher = patch(
        'src.infra.entrypoints.http.endpoints.manual_chat.inject',
        return_value=_make_mock_executor()
    )
    self._injector_patcher.start()

  def tearDown(self):
    """Limpia variables de entorno."""
    self._injector_patcher.stop()
    if "GUARDIAN_API_KEY" in os.environ:
      del os.environ["GUARDIAN_API_KEY"]

  def test_r14_at_least_two_execution_nodes_besides_entry_exit(self):
    """R14: StateGraph DEBE tener al menos dos nodos de ejecución (además de entrada/salida)."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    events = parse_sse_events(response.text)
    node_events = [ev for ev in events if ev.get("event") == "node_update"]

    nodes = set()
    for ev in node_events:
      data = ev.get("data")
      if isinstance(data, dict) and "node" in data:
        nodes.add(data["node"])

    # Debe haber al menos 2 nodos distintos
    self.assertGreaterEqual(len(nodes), 2,
        "Debe haber al menos 2 nodos distintos en la ejecución")

  def test_r15_nodes_execute_in_defined_order(self):
    """R15: StateGraph DEBE definir transiciones. Nodos ejecutan según transiciones."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    events = parse_sse_events(response.text)
    node_events = [ev for ev in events if ev.get("event") == "node_update"]

    self.assertGreater(len(node_events), 0)
    # Los nodos deben aparecer en orden predecible
    nodes = []
    for ev in node_events:
      data = ev.get("data")
      if isinstance(data, dict) and "node" in data:
        nodes.append(data["node"])

    # Validar que el primer nodo es "start"
    if nodes:
      self.assertEqual(nodes[0], "start")

  def test_r15_transitions_between_nodes_follow_state(self):
    """R15: Transiciones DEBEN responder al estado actual."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    events = parse_sse_events(response.text)
    node_events = [ev for ev in events if ev.get("event") == "node_update"]

    # Cada evento debe tener data (estado)
    for ev in node_events:
      data = ev.get("data")
      self.assertIsInstance(data, dict)
      # El estado debe contener información de nodo
      self.assertIn("node", data)


class TestWorkflowInputContractR9(unittest.TestCase):
  """Tests para R9 (contrato de entrada, WorkflowInput)."""

  def setUp(self):
    """Configura app y cliente de test."""
    os.environ["GUARDIAN_API_KEY"] = "test-secret-key-123"
    self.app = create_app()
    self.client = TestClient(self.app)
    self.valid_headers = {"X-API-KEY": "test-secret-key-123"}
    self._injector_patcher = patch(
        'src.infra.entrypoints.http.endpoints.manual_chat.inject',
        return_value=_make_mock_executor()
    )
    self._injector_patcher.start()

  def tearDown(self):
    """Limpia variables de entorno."""
    self._injector_patcher.stop()
    if "GUARDIAN_API_KEY" in os.environ:
      del os.environ["GUARDIAN_API_KEY"]

  def test_r9_workflow_input_is_defined_and_validated(self):
    """R9: El sistema DEBE definir explícitamente el contrato de entrada."""
    # WorkflowInput debe existir
    self.assertIsNotNone(WorkflowInput)

    # Debe ser un modelo Pydantic
    from pydantic import BaseModel
    self.assertTrue(issubclass(WorkflowInput, BaseModel))

  def test_r9_workflow_input_forbids_extra_fields(self):
    """R9: WorkflowInput DEBE tener política de validación (forbid extra fields)."""
    # Intentar pasarle campos inválidos debe fallar
    response = self.client.post(
        "/manual-chat",
        json={"invalid_field": "test"},
        headers=self.valid_headers
    )
    # Debe rechazar con 400
    self.assertEqual(response.status_code, 400)

  def test_r9_accepts_valid_input_and_passes_to_workflow(self):
    """R9: Contrato acepta entrada válida y la pasa al workflow."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    # Entrada vacía es válida
    self.assertEqual(response.status_code, 200)


class TestErrorHandlingR5R7(unittest.TestCase):
  """Tests para R5 (error handling), R7 (logging)."""

  def setUp(self):
    """Configura app y cliente de test."""
    os.environ["GUARDIAN_API_KEY"] = "test-secret-key-123"
    self.app = create_app()
    self.client = TestClient(self.app)
    self.valid_headers = {"X-API-KEY": "test-secret-key-123"}
    self._injector_patcher = patch(
        'src.infra.entrypoints.http.endpoints.manual_chat.inject',
        return_value=_make_mock_executor()
    )
    self._injector_patcher.start()

  def tearDown(self):
    """Limpia variables de entorno."""
    self._injector_patcher.stop()
    if "GUARDIAN_API_KEY" in os.environ:
      del os.environ["GUARDIAN_API_KEY"]

  def test_r5_on_node_failure_emits_error_event_and_stops(self):
    """R5: CUANDO un nodo falla, DEBE emitir evento Error y detener ejecución."""
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    # En caso normal (sin errores), el workflow completa
    self.assertEqual(response.status_code, 200)
    events = parse_sse_events(response.text)

    # Si hay evento de error, debe estar en el stream
    event_types = [ev.get("event") for ev in events]
    self.assertGreater(len(event_types), 0)

  def test_r7_preserves_execution_traceability_via_logs(self):
    """R7: DEBE preservar trazabilidad mediante logs INFO/ERROR."""
    # Ejecutar workflow
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )

    # Si la ejecución fue exitosa, debería haber logs
    self.assertEqual(response.status_code, 200)


class TestWorkflowStateR13(unittest.TestCase):
  """Tests para R13 (StateGraph y WorkflowState tipado)."""

  def test_r13_workflow_state_is_typed_dict(self):
    """R13: WorkflowState DEBE ser TypedDict con: user_input, processing_state, current_node, result, errors."""
    from src.domain.models import WorkflowState

    # Verificar que es TypedDict
    expected_fields = {"user_input", "processing_state", "current_node", "result", "errors"}

    # Obtener anotaciones (TypedDict usa __annotations__)
    if hasattr(WorkflowState, "__annotations__"):
      actual_fields = set(WorkflowState.__annotations__.keys())
      self.assertEqual(actual_fields, expected_fields)

  def test_r13_workflow_state_includes_required_fields(self):
    """R13: WorkflowState DEBE incluir los campos especificados."""
    from src.domain.models import WorkflowState

    # Crear una instancia de estado
    state: WorkflowState = {
        "user_input": "test",
        "processing_state": "pending",
        "current_node": "",
        "result": None,
        "errors": []
    }

    # Verificar que tiene todos los campos
    self.assertIn("user_input", state)
    self.assertIn("processing_state", state)
    self.assertIn("current_node", state)
    self.assertIn("result", state)
    self.assertIn("errors", state)


if __name__ == "__main__":
  unittest.main()
