import logging

from src.domain.models import AgentState, ClonePathError
from src.infra.adapters.workflow.log import with_logging
from src.infra.helper import inject, InPortType

logger = logging.getLogger(__name__)


@with_logging()
async def node_clone_repository(state: AgentState) -> AgentState:
  """
  Nodo independiente para clonación del repositorio.

  Responsabilidades:
    1. Extraer URL del repositorio
    2. Extraer token de autenticación (opcional)
    3. Clonar repositorio en /tmp/guardian/<uuid>/
    4. Escribir clone_path en estado

  Args:
    state: AgentState con repository.url y repository.installation (opcional)

  Returns:
    AgentState con clone_path

  Raises:
    ClonePathError: Si clonación falla
  """
  try:
    repository = state.get("repository", {})
    repo_url = (
      repository.get("url")
      if isinstance(repository, dict)
      else repository.url
    )
    installation_token = (
      repository.get("installation")
      if isinstance(repository, dict)
      else getattr(repository, "installation", None)
    )

    if not repo_url:
      logger.error("[CLONE_REPOSITORY] Falta repository.url")
      raise ClonePathError("Falta 'repository.url' en estado")

    logger.info(
      f"[CLONE_REPOSITORY] Clonando: url={repo_url}, "
      f"has_token={bool(installation_token)}"
    )

    clone_service = inject(InPortType.CloneService)
    clone_path = clone_service.clone_repository(repo_url, installation_token)

    state["clone_path"] = clone_path

    return state

  except ClonePathError as e:
    logger.error(f"[CLONE_REPOSITORY] ClonePathError: {e}")
    raise

  except Exception as e:
    logger.error(f"[CLONE_REPOSITORY] Error inesperado: {e}")
    raise ClonePathError(f"Error inesperado en nodo clone_repository: {e}")
