import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from src.domain.models import WorkflowInput, WorkflowState
from src.infra.adapters.workflow import WorkflowBuilder, WorkflowEngine
from src.infra.entrypoints.http.middlewares import validate_api_key
from src.infra.entrypoints.http.errors import WorkflowValidationError

logger = logging.getLogger(__name__)

manual_chat_router = APIRouter(
  prefix="/manual-chat",
  tags=["manual-chat"]
)


async def _stream_workflow_events(
    builder: WorkflowBuilder, input_data: WorkflowInput
) -> AsyncGenerator[str, None]:
  """Itera eventos del workflow y los emite como JSONL."""
  try:
    graph = builder.build()
    engine = WorkflowEngine(graph)

    initial_state: WorkflowState = {
        "user_input": input_data.user_input if hasattr(input_data, "user_input") else "",
        "processing_state": "pending",
        "current_node": "",
        "result": None,
        "errors": []
    }

    async for event in engine.execute_and_stream(initial_state):
      yield json.dumps(event) + "\n"

  except Exception as e:
    logger.error(f"Workflow streaming error: {str(e)}")
    error_event = {
        "event_type": "error",
        "node": "engine",
        "data": {"error": str(e)}
    }
    yield json.dumps(error_event) + "\n"


@manual_chat_router.post("")
async def manual_chat(
    request: Request, _ = Depends(validate_api_key)
) -> StreamingResponse:
  """Endpoint que ejecuta workflow y retorna stream de eventos."""
  try:
    body = await request.json()
  except json.JSONDecodeError as e:
    raise WorkflowValidationError(f"Invalid JSON: {str(e)}")

  try:
    input_data = WorkflowInput(**body)
  except ValidationError as e:
    logger.warning(f"Validation error: {str(e)}")
    raise WorkflowValidationError(f"Invalid request body: {str(e)}")

  logger.info("Starting workflow execution")
  builder = WorkflowBuilder()

  return StreamingResponse(
    _stream_workflow_events(builder, input_data),
    media_type="application/x-ndjson"
  )