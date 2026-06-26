import logging

from src.domain.models import AgentState, ClonePathError, CheckoutError
from src.infra.adapters.workflow.log import with_logging
from src.infra.helper import inject, InPortType

logger = logging.getLogger(__name__)


@with_logging()
async def node_checkout_commit(state: AgentState) -> AgentState:
  """
  Nodo independiente para checkout a commit específico.

  Responsabilidades:
    1. Extraer clone_path y commit_sha del estado
    2. Hacer checkout al commit especificado
    3. Lanzar excepción si commit no existe

  Args:
    state: AgentState con clone_path y repository.commit_sha

  Returns:
    AgentState sin cambios (checkout es operación in-place)

  Raises:
    CheckoutError: Si commit no existe o checkout falla
    ClonePathError: Si información requerida falta
  """
  try:
    clone_path = state.get("clone_path")
    repository = state.get("repository", {})
    commit_sha = (
      repository.get("commit_sha")
      if isinstance(repository, dict)
      else getattr(repository, "commit_sha", None)
    )

    if not clone_path:
      logger.error("[CHECKOUT_COMMIT] Falta clone_path")
      raise ClonePathError("Falta 'clone_path' en estado")

    if not commit_sha:
      logger.error("[CHECKOUT_COMMIT] Falta repository.commit_sha")
      raise ClonePathError("Falta 'repository.commit_sha' en estado")

    logger.info(f"[CHECKOUT_COMMIT] commit_sha={commit_sha}")

    clone_service = inject(InPortType.CloneService)
    clone_service.checkout_commit(clone_path, commit_sha)

    return state

  except (CheckoutError, ClonePathError) as e:
    logger.error(f"[CHECKOUT_COMMIT] Error: {e}")
    raise

  except Exception as e:
    logger.error(f"[CHECKOUT_COMMIT] Error inesperado: {e}")
    raise CheckoutError(f"Error inesperado en nodo checkout_commit: {e}")
