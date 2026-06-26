import logging
from typing import Set

from src.domain.models import AgentState, ClonePathError
from src.infra.adapters.workflow.log import with_logging
from src.infra.helper import inject, InPortType

logger = logging.getLogger(__name__)


@with_logging()
async def node_replace_files_content(state: AgentState) -> AgentState:
  """
  Nodo independiente para reemplazo de contenido de archivos.

  Responsabilidades:
    1. Extraer clone_path y files_content del estado
    2. Reemplazar contenido de archivos en el repositorio clonado
    3. Registrar qué archivos fueron modificados
    4. Escribir _replaced_files en estado (interno para generate_diff)

  Args:
    state: AgentState con clone_path y files_content

  Returns:
    AgentState con _replaced_files (set de rutas relativas reemplazadas)

  Raises:
    ClonePathError: Si reemplazo falla o información requerida falta
  """
  try:
    clone_path = state.get("clone_path")
    files_content = state.get("files_content", [])

    if not clone_path:
      logger.error("[REPLACE_FILES_CONTENT] Falta clone_path")
      raise ClonePathError("Falta 'clone_path' en estado")

    if not files_content:
      logger.warning("[REPLACE_FILES_CONTENT] files_content vacío")
      state["_replaced_files"] = set()
      return state

    logger.info(
      f"[REPLACE_FILES_CONTENT] "
      f"Reemplazando {len(files_content)} archivos"
    )

    clone_service = inject(InPortType.CloneService)
    replaced_files: Set[str] = clone_service.replace_files_content(
      clone_path,
      files_content
    )

    state["_replaced_files"] = replaced_files

    return state

  except ClonePathError as e:
    logger.error(f"[REPLACE_FILES_CONTENT] ClonePathError: {e}")
    raise

  except Exception as e:
    logger.error(f"[REPLACE_FILES_CONTENT] Error inesperado: {e}")
    raise ClonePathError(
      f"Error inesperado en nodo replace_files_content: {e}"
    )
