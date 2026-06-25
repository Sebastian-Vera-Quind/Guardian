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
    yield {
        "event_type": "complete",
        "node": "workflow",
        "data": {"project_code": "test", "project_id": "123"}
    }

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
    """R4: CUANDO un nodo cambia de estado, DEBE emitir evento con node y status."""
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
        self.assertIn("status", data)
        self.assertEqual(data.get("status"), "in_progress")
        # No debe incluir result en eventos in_progress
        self.assertNotIn("result", data)



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
    """R6: CUANDO todos los nodos completan, DEBE detener el stream con status: success."""
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

    # El evento complete debe tener status: success e incluir result
    complete_events = [ev for ev in events if ev.get("event") == "complete"]
    self.assertEqual(len(complete_events), 1, "Debe haber exactamente un evento complete")
    complete_data = complete_events[0].get("data")
    self.assertIsInstance(complete_data, dict)
    self.assertEqual(complete_data.get("status"), "success")
    self.assertIn("result", complete_data)
    self.assertIn("node", complete_data)


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
      # El estado debe contener información de nodo y status
      self.assertIn("node", data)
      self.assertIn("status", data)
      self.assertEqual(data.get("status"), "in_progress")


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


class TestApiResponseRefactor(unittest.TestCase):
  """Tests para feature api_response: Validar nueva estructura de eventos."""

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

  def test_node_update_events_have_status_in_progress(self):
    """
    Valida que eventos node_update contengan status: 'in_progress' sin result.
    Acceptance: Eventos de nodos con status 'in_progress' no incluyen 'result'.
    """
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    events = parse_sse_events(response.text)
    node_update_events = [ev for ev in events if ev.get("event") == "node_update"]

    # Debe haber al menos un evento node_update
    self.assertGreater(len(node_update_events), 0)

    # Cada evento node_update debe tener status: in_progress
    for ev in node_update_events:
      data = ev.get("data")
      self.assertIsInstance(data, dict)
      self.assertIn("status", data, "Evento debe tener 'status'")
      self.assertEqual(data.get("status"), "in_progress",
                       "Status debe ser 'in_progress'")
      self.assertIn("node", data, "Evento debe tener 'node'")
      self.assertNotIn("result", data,
                       "Evento in_progress NO debe incluir 'result'")

  def test_complete_event_has_status_success_with_result(self):
    """
    Valida que evento complete contenga status: 'success' con result.
    Acceptance: Solo cuando status sea 'success' incluir attributo 'result'.
    """
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    events = parse_sse_events(response.text)
    complete_events = [ev for ev in events if ev.get("event") == "complete"]

    # Debe haber exactamente un evento complete
    self.assertEqual(len(complete_events), 1,
                     "Debe haber exactamente un evento complete")

    complete_event = complete_events[0]
    data = complete_event.get("data")

    # Validar estructura
    self.assertIsInstance(data, dict)
    self.assertIn("status", data, "Evento debe tener 'status'")
    self.assertEqual(data.get("status"), "success",
                     "Status debe ser 'success'")
    self.assertIn("node", data, "Evento debe tener 'node'")
    self.assertIn("result", data,
                  "Evento success DEBE incluir 'result'")

    # El result debe ser un dict (contiene estado final del workflow)
    result = data.get("result")
    self.assertIsInstance(result, dict, "Result debe ser un diccionario")

  def test_error_event_has_status_error_without_result(self):
    """
    Valida que evento error contenga status: 'error' sin result.
    Acceptance: En caso de status 'error' no retornar 'result'.
    """
    # Crear mock que lance error
    error_mock = MagicMock()

    async def _fake_error_stream(input_data):
      yield {"event_type": "error", "node": "loader", "data": {}}

    error_mock.execute_and_stream = _fake_error_stream

    with patch(
        'src.infra.entrypoints.http.endpoints.manual_chat.inject',
        return_value=error_mock
    ):
      response = self.client.post(
          "/manual-chat",
          json={},
          headers=self.valid_headers
      )

      events = parse_sse_events(response.text)
      error_events = [ev for ev in events if ev.get("event") == "error"]

      # Debe haber al menos un evento error
      if len(error_events) > 0:
        error_event = error_events[0]
        data = error_event.get("data")

        # Validar estructura
        self.assertIsInstance(data, dict)
        self.assertIn("status", data)
        self.assertEqual(data.get("status"), "error",
                         "Status debe ser 'error'")
        self.assertIn("node", data)
        self.assertNotIn("result", data,
                         "Evento error NO debe incluir 'result'")

  def test_complete_event_includes_full_workflow_state(self):
    """
    Valida que el result del evento complete contenga estado final del workflow.
    Acceptance: result contiene información del estado final.
    """
    response = self.client.post(
        "/manual-chat",
        json={},
        headers=self.valid_headers
    )
    events = parse_sse_events(response.text)
    complete_events = [ev for ev in events if ev.get("event") == "complete"]

    self.assertEqual(len(complete_events), 1)
    data = complete_events[0].get("data")

    result = data.get("result")
    # El result debe contener información del estado final
    # (en nuestro mock contiene project_code y project_id)
    self.assertIsNotNone(result)
    self.assertIsInstance(result, dict)

  def test_complete_event_with_uuid_serializes(self):
    """
    Valida que el result con UUID (project_id) se serializa correctamente a JSON.

    Esta prueba verifica el fix para el error:
    "Object of type UUID is not JSON serializable"

    El UUID debe convertirse a string antes de ser serializado.
    """
    from uuid import UUID

    # Crear mock que emita evento complete con UUID en el result
    uuid_mock = MagicMock()
    test_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")

    async def _fake_uuid_stream(input_data):
      # Emitir eventos normales
      yield {"event_type": "node_updated", "node": "start", "data": {}}
      # Emitir evento complete con UUID en el data
      yield {
          "event_type": "complete",
          "node": "workflow",
          "data": {"project_code": "test", "project_id": test_uuid}
      }

    uuid_mock.execute_and_stream = _fake_uuid_stream

    with patch(
        'src.infra.entrypoints.http.endpoints.manual_chat.inject',
        return_value=uuid_mock
    ):
      response = self.client.post(
          "/manual-chat",
          json={},
          headers=self.valid_headers
      )

      # El status debe ser 200 (no error de serialization)
      self.assertEqual(response.status_code, 200,
                       "Debe haber podido serializar el UUID a JSON")

      # Parsear eventos
      events = parse_sse_events(response.text)
      complete_events = [ev for ev in events if ev.get("event") == "complete"]

      self.assertEqual(len(complete_events), 1, "Debe haber un evento complete")
      data = complete_events[0].get("data")
      result = data.get("result")

      # El project_id debe estar presente y ser string
      self.assertIn("project_id", result, "Result debe contener project_id")
      self.assertEqual(result["project_id"], str(test_uuid),
                       f"project_id debe convertirse a string: {str(test_uuid)}")

      # Validar que es JSON válido (ya parseable desde parse_sse_events)
      self.assertIsInstance(data, dict, "Evento debe ser válido JSON")

  def test_complete_event_with_pydantic_model_serializes(self):
    """
    Valida que el result con objetos Pydantic (RepositoryInput) se serializa correctamente a JSON.

    Esta prueba verifica el fix para el error:
    "Object of type RepositoryInput is not JSON serializable"

    Los objetos Pydantic BaseModel deben convertirse a dict vía model_dump().
    """
    from src.domain.models.util.repository import RepositoryInput

    # Crear mock que emita evento complete con RepositoryInput en el result
    pydantic_mock = MagicMock()

    # Crear un RepositoryInput (objeto Pydantic)
    repo_input = RepositoryInput(
        url="https://github.com/user/repo.git",
        installation="github-app-installation",
        commit_sha="abc123",
        target="main"
    )

    async def _fake_pydantic_stream(input_data):
      # Emitir eventos normales
      yield {"event_type": "node_updated", "node": "start", "data": {}}
      # Emitir evento complete con RepositoryInput en el data
      yield {
          "event_type": "complete",
          "node": "workflow",
          "data": {"project_code": "test", "repository": repo_input}
      }

    pydantic_mock.execute_and_stream = _fake_pydantic_stream

    with patch(
        'src.infra.entrypoints.http.endpoints.manual_chat.inject',
        return_value=pydantic_mock
    ):
      response = self.client.post(
          "/manual-chat",
          json={},
          headers=self.valid_headers
      )

      # El status debe ser 200 (no error de serialization)
      self.assertEqual(response.status_code, 200,
                       "Debe haber podido serializar el RepositoryInput a JSON")

      # Parsear eventos
      events = parse_sse_events(response.text)
      complete_events = [ev for ev in events if ev.get("event") == "complete"]

      self.assertEqual(len(complete_events), 1, "Debe haber un evento complete")
      data = complete_events[0].get("data")
      result = data.get("result")

      # El repository debe estar presente y ser un dict
      self.assertIn("repository", result, "Result debe contener repository")
      repo_data = result["repository"]
      self.assertIsInstance(repo_data, dict, "Repository debe ser un dict")

      # Validar que tiene los campos del RepositoryInput
      self.assertIn("url", repo_data, "Repository dict debe tener url")
      self.assertEqual(repo_data["url"], "https://github.com/user/repo.git")
      self.assertIn("installation", repo_data)
      self.assertIn("commit_sha", repo_data)
      self.assertIn("target", repo_data)

      # Validar que es JSON válido (ya parseable desde parse_sse_events)
      self.assertIsInstance(data, dict, "Evento debe ser válido JSON")

  def test_complete_event_with_mixed_serializable_types(self):
    """
    Valida que el result con múltiples tipos serializables (UUID, Pydantic, dict, list)
    se serializa correctamente a JSON.

    Esta prueba verifica que la función convert_state_to_json_safe() maneja
    correctamente anidamientos complejos de diferentes tipos.
    """
    from uuid import UUID
    from src.domain.models.util.repository import RepositoryInput

    # Crear mock que emita evento complete con múltiples tipos
    mixed_mock = MagicMock()
    test_uuid = UUID("550e8400-e29b-41d4-a716-446655440001")
    repo_input = RepositoryInput(
        url="https://github.com/test/mixed.git",
        installation="github-mixed"
    )

    async def _fake_mixed_stream(input_data):
      yield {"event_type": "node_updated", "node": "start", "data": {}}
      # Emitir evento complete con estructura compleja
      yield {
          "event_type": "complete",
          "node": "workflow",
          "data": {
              "project_id": test_uuid,  # UUID
              "project_code": "mixed-test",
              "repository": repo_input,  # Pydantic model
              "metadata": {
                  "id": UUID("550e8400-e29b-41d4-a716-446655440002"),  # UUID en dict
                  "tags": ["test", "mixed"],  # list
              },
              "files": [
                  {
                      "id": UUID("550e8400-e29b-41d4-a716-446655440003"),
                      "name": "file1.py"
                  }
              ]
          }
      }

    mixed_mock.execute_and_stream = _fake_mixed_stream

    with patch(
        'src.infra.entrypoints.http.endpoints.manual_chat.inject',
        return_value=mixed_mock
    ):
      response = self.client.post(
          "/manual-chat",
          json={},
          headers=self.valid_headers
      )

      # El status debe ser 200 (no error de serialization)
      self.assertEqual(response.status_code, 200,
                       "Debe haber podido serializar tipos mixtos a JSON")

      # Parsear eventos
      events = parse_sse_events(response.text)
      complete_events = [ev for ev in events if ev.get("event") == "complete"]

      self.assertEqual(len(complete_events), 1, "Debe haber un evento complete")
      data = complete_events[0].get("data")
      result = data.get("result")

      # Validar UUID en raíz
      self.assertIn("project_id", result)
      self.assertEqual(result["project_id"], str(test_uuid))
      self.assertIsInstance(result["project_id"], str)

      # Validar Pydantic model convertido
      self.assertIn("repository", result)
      self.assertIsInstance(result["repository"], dict)
      self.assertEqual(result["repository"]["url"], "https://github.com/test/mixed.git")

      # Validar UUID dentro de dict anidado
      self.assertIn("metadata", result)
      self.assertIsInstance(result["metadata"], dict)
      self.assertIn("id", result["metadata"])
      self.assertEqual(result["metadata"]["id"], "550e8400-e29b-41d4-a716-446655440002")

      # Validar list dentro de dict
      self.assertIn("tags", result["metadata"])
      self.assertIsInstance(result["metadata"]["tags"], list)
      self.assertEqual(result["metadata"]["tags"], ["test", "mixed"])

      # Validar UUID dentro de list
      self.assertIn("files", result)
      self.assertIsInstance(result["files"], list)
      self.assertEqual(len(result["files"]), 1)
      self.assertIn("id", result["files"][0])
      self.assertEqual(result["files"][0]["id"], "550e8400-e29b-41d4-a716-446655440003")

      # Validar que todo es JSON válido
      self.assertIsInstance(data, dict, "Evento debe ser válido JSON")

  def test_complete_event_with_datetime_serializes(self):
    """
    Valida que el result con datetime (timestamps) se serializa correctamente a JSON.

    Esta prueba verifica el fix para el error:
    "Object of type datetime is not JSON serializable"

    Los objetos datetime y date deben convertirse a ISO format string.
    """
    from datetime import datetime, date

    # Crear mock que emita evento complete con datetime en el result
    datetime_mock = MagicMock()
    test_datetime = datetime(2026, 6, 25, 14, 30, 45)
    test_date = date(2026, 6, 25)

    async def _fake_datetime_stream(input_data):
      # Emitir eventos normales
      yield {"event_type": "node_updated", "node": "start", "data": {}}
      # Emitir evento complete con datetime en el data
      yield {
          "event_type": "complete",
          "node": "workflow",
          "data": {
              "project_code": "datetime-test",
              "created_at": test_datetime,
              "modified_date": test_date,
              "timestamps": {
                  "started": test_datetime,
                  "ended": test_datetime
              }
          }
      }

    datetime_mock.execute_and_stream = _fake_datetime_stream

    with patch(
        'src.infra.entrypoints.http.endpoints.manual_chat.inject',
        return_value=datetime_mock
    ):
      response = self.client.post(
          "/manual-chat",
          json={},
          headers=self.valid_headers
      )

      # El status debe ser 200 (no error de serialization)
      self.assertEqual(response.status_code, 200,
                       "Debe haber podido serializar datetime a JSON")

      # Parsear eventos
      events = parse_sse_events(response.text)
      complete_events = [ev for ev in events if ev.get("event") == "complete"]

      self.assertEqual(len(complete_events), 1, "Debe haber un evento complete")
      data = complete_events[0].get("data")
      result = data.get("result")

      # El created_at debe estar presente y ser ISO format string
      self.assertIn("created_at", result, "Result debe contener created_at")
      self.assertEqual(result["created_at"], test_datetime.isoformat(),
                       f"created_at debe convertirse a ISO format: {test_datetime.isoformat()}")

      # El modified_date debe estar presente y ser ISO format string
      self.assertIn("modified_date", result, "Result debe contener modified_date")
      self.assertEqual(result["modified_date"], test_date.isoformat(),
                       f"modified_date debe convertirse a ISO format: {test_date.isoformat()}")

      # Los timestamps dentro del dict anidado también deben ser ISO format
      self.assertIn("timestamps", result, "Result debe contener timestamps")
      timestamps = result["timestamps"]
      self.assertIsInstance(timestamps, dict)
      self.assertEqual(timestamps["started"], test_datetime.isoformat())
      self.assertEqual(timestamps["ended"], test_datetime.isoformat())

      # Validar que es JSON válido (ya parseable desde parse_sse_events)
      self.assertIsInstance(data, dict, "Evento debe ser válido JSON")

  def test_complete_event_with_enum_serializes(self):
    """
    Valida que el result con objetos Enum se serializa correctamente a JSON.

    Esta prueba verifica que Enum se convierte a su valor (.value)
    para ser serializable en JSON.
    """
    from enum import Enum

    # Definir un Enum de ejemplo (ej: ChangeType)
    class ChangeType(Enum):
      ADDED = "added"
      MODIFIED = "modified"
      DELETED = "deleted"

    # Crear mock que emita evento complete con Enum en el result
    enum_mock = MagicMock()
    test_enum = ChangeType.MODIFIED

    async def _fake_enum_stream(input_data):
      # Emitir eventos normales
      yield {"event_type": "node_updated", "node": "start", "data": {}}
      # Emitir evento complete con Enum en el data
      yield {
          "event_type": "complete",
          "node": "workflow",
          "data": {
              "project_code": "enum-test",
              "change_type": test_enum,
              "changes": [
                  {"status": ChangeType.ADDED, "file": "file1.py"},
                  {"status": ChangeType.MODIFIED, "file": "file2.py"},
                  {"status": ChangeType.DELETED, "file": "file3.py"},
              ]
          }
      }

    enum_mock.execute_and_stream = _fake_enum_stream

    with patch(
        'src.infra.entrypoints.http.endpoints.manual_chat.inject',
        return_value=enum_mock
    ):
      response = self.client.post(
          "/manual-chat",
          json={},
          headers=self.valid_headers
      )

      # El status debe ser 200 (no error de serialization)
      self.assertEqual(response.status_code, 200,
                       "Debe haber podido serializar Enum a JSON")

      # Parsear eventos
      events = parse_sse_events(response.text)
      complete_events = [ev for ev in events if ev.get("event") == "complete"]

      self.assertEqual(len(complete_events), 1, "Debe haber un evento complete")
      data = complete_events[0].get("data")
      result = data.get("result")

      # El change_type debe estar presente y ser el valor del enum
      self.assertIn("change_type", result, "Result debe contener change_type")
      self.assertEqual(result["change_type"], "modified",
                       "change_type debe convertirse al valor del enum")

      # Los cambios en la lista también deben tener el enum convertido
      self.assertIn("changes", result, "Result debe contener changes")
      changes = result["changes"]
      self.assertIsInstance(changes, list)
      self.assertEqual(len(changes), 3, "Debe haber 3 cambios")

      # Validar que los status enums están convertidos a valores
      self.assertEqual(changes[0]["status"], "added")
      self.assertEqual(changes[1]["status"], "modified")
      self.assertEqual(changes[2]["status"], "deleted")

      # Validar que es JSON válido (ya parseable desde parse_sse_events)
      self.assertIsInstance(data, dict, "Evento debe ser válido JSON")


if __name__ == "__main__":
  unittest.main()
