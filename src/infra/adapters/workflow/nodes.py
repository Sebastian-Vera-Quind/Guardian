from src.domain.models import WorkflowState


async def node_start(state: WorkflowState) -> dict:
  """Nodo inicial: valida entrada y prepara estado."""
  return {
    "processing_state": "processing",
    "current_node": "start"
  }


async def node_process(state: WorkflowState) -> dict:
  """Nodo de procesamiento: ejecuta lógica de negocio."""
  result = {"processed": True}
  return {
    "current_node": "process",
    "result": result,
    "processing_state": "done"
  }


async def node_end(state: WorkflowState) -> dict:
  """Nodo final: completa el workflow."""
  return {"current_node": "end"}
