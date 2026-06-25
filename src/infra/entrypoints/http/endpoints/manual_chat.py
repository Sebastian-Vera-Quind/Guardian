import json
import logging
import asyncio
from enum import Enum
from json import JSONEncoder
from datetime import datetime, date
from typing import AsyncGenerator, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import EventSourceResponse
from pydantic import ValidationError, BaseModel

from src.infra.helper import inject, InPortType
from src.domain.models import WorkflowInput, WorkflowState
from src.infra.entrypoints.http.middlewares import validate_api_key
from src.infra.entrypoints.http.errors import WorkflowValidationError

logger = logging.getLogger(__name__)


class SafeJSONEncoder(JSONEncoder):
    """Custom JSON encoder que maneja UUID, datetime, date, Enum, y Pydantic BaseModel."""

    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        try:
            return str(obj)
        except Exception:
            return None




manual_chat_router = APIRouter(
  prefix="/manual-chat",
  tags=["manual-chat"]
)

# Configuración de timeouts y keepalive
WORKFLOW_TIMEOUT_SECONDS = 300
KEEPALIVE_INTERVAL_SECONDS = 15


async def event_stream(input_data: WorkflowInput) -> AsyncGenerator[str, None]:
  q: asyncio.Queue[tuple[str, object]] = asyncio.Queue()

  async def _produce() -> None:
    """Productor que itera eventos del workflow."""
    try:
      engine = inject(InPortType.WorkFlowExcecutor)

      async for event in engine.execute_and_stream(input_data):
        await q.put(("event", event))
    except Exception as exc:
      await q.put(("error", exc))
    else:
      await q.put(("done", None))

  # Inicia el productor en background
  producer = asyncio.create_task(_produce())
  loop = asyncio.get_running_loop()
  deadline = loop.time() + WORKFLOW_TIMEOUT_SECONDS

  try:
    while True:
      # Calcula tiempo restante
      remaining = deadline - loop.time()
      if remaining <= 0:
        raise asyncio.TimeoutError("Workflow execution timeout")

      wait = min(KEEPALIVE_INTERVAL_SECONDS, remaining)

      try:
        tag, payload = await asyncio.wait_for(q.get(), timeout=wait)
      except asyncio.TimeoutError:
        # Envía keepalive para mantener la conexión viva
        yield f'event: keepalive\ndata: {{"message": "processing"}}\n\n'
        continue

      if tag == "done":
        # Workflow completado exitosamente
        logger.info("Workflow completed successfully")
        break
      elif tag == "error":
        # Error durante la ejecución
        raise payload

      # Evento del workflow
      ev = payload
      event_type = ev.get("event_type", "unknown")

      if event_type == "complete":
        # Evento de finalización con estado final
        # SafeJSONEncoder maneja automáticamente UUID, datetime, date, y BaseModel
        event_data = {
            "status": "success",
            "node": ev.get("node", "workflow"),
            "result": ev.get("data", {})
        }
        yield f'event: complete\ndata: {json.dumps(event_data, cls=SafeJSONEncoder)}\n\n'
      else:
        # Evento de nodo en progreso
        event_data = {
            "status": "in_progress",
            "node": ev.get("node", "unknown"),
        }
        yield f'event: node_update\ndata: {json.dumps(event_data, cls=SafeJSONEncoder)}\n\n'

  except asyncio.TimeoutError as e:
    logger.error(f"Workflow execution timeout: {str(e)}")
    event_data = {
        "status": "error",
        "node": "workflow",
    }
    yield f'event: error\ndata: {json.dumps(event_data, cls=SafeJSONEncoder)}\n\n'
  except Exception as e:
    logger.error(f"Workflow streaming error: {str(e)}", exc_info=True)
    event_data = {
        "status": "error",
        "node": "workflow",
    }
    yield f'event: error\ndata: {json.dumps(event_data, cls=SafeJSONEncoder)}\n\n'
  finally:
    # Cancela el productor si sigue corriendo
    if not producer.done():
      producer.cancel()
      try:
        await producer
      except asyncio.CancelledError:
        pass
      except Exception as cleanup_exc:
        logger.debug(f"Producer cleanup exception: {cleanup_exc}")


@manual_chat_router.post("")
async def manual_chat(
    request: Request, _ = Depends(validate_api_key)
) -> EventSourceResponse:
  """
  Endpoint que ejecuta workflow y retorna SSE stream de eventos.

  Protocolo SSE:
  - event: keepalive → Mantiene conexión viva durante procesamiento
  - event: node_update → Evento de estado de nodo
  - event: complete → Workflow completado exitosamente
  - event: error → Error durante ejecución
  """
  try:
    body = await request.json()
    input_data = WorkflowInput(**body)
  except ValidationError as e:
    logger.warning(f"Validation error: {str(e.errors())}")
    raise WorkflowValidationError("Invalid request body")
  except json.JSONDecodeError as e:
    raise WorkflowValidationError("Invalid JSON")

  logger.info("Starting workflow execution")

  return EventSourceResponse(event_stream(input_data))
