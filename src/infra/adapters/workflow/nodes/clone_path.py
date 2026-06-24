import logging

from src.domain.models import AgentState, ClonePathError, DiffGenerationError
from src.infra.adapters.workflow.log import with_logging
from src.infra.helper import inject, InPortType

logger = logging.getLogger(__name__)


@with_logging()
async def node_clone_task(state: AgentState) -> AgentState:
  """
  Nodo de clonación, checkout y análisis de diferencias.

  Responsabilidades:
    1. Validar que load_to == "clone"
    2. Inyectar CloneService
    3. Clonar repositorio en /tmp/guardian/<uuid>/
    4. Hacer checkout a commit_sha
    5. Generar diff si target está presente
    6. Construir project_tree
    7. Escribir clone_path, diff, modified_lines, project_tree en estado

  Args:
    state: AgentState con load_to, repository, metadata

  Returns:
    AgentState con clone_path, diff, modified_lines, project_tree

  Raises:
    ClonePathError: Si clonación o checkout fallan (R12, R13, R17)
    DiffGenerationError: Si generación de diff falla (R14)
  """
  try:
    load_to = state.get("load_to")
    if load_to != "clone":
      logger.error(f"[CLONE_PATH] load_to debe ser 'clone', pero es: {load_to}")
      raise ClonePathError(
        f"El nodo clone_path requiere load_to='clone', recibió: {load_to}"
      )

    repository = state.get("repository", {})
    repo_url = repository.get("url")
    installation_token = repository.get("installation")
    commit_sha = repository.get("commit_sha")
    target = repository.get("target")

    if not repo_url or not commit_sha:
      logger.error(
        f"[CLONE_PATH] Falta información requerida: "
        f"url={repo_url}, commit_sha={commit_sha}"
      )
      raise ClonePathError(
        "Falta información requerida en 'repository': url y commit_sha"
      )

    logger.info(
      f"[CLONE_PATH] Parámetros: "
      f"url={repo_url}, "
      f"has_token={bool(installation_token)}, "
      f"commit_sha={commit_sha}, "
      f"target={target}"
    )

    clone_service = inject(InPortType.CloneService)

    result = clone_service.clone(
      repo_url=repo_url,
      installation_token=installation_token,
      commit_sha=commit_sha,
      target=target
    )

    state["clone_path"] = result["clone_path"]
    if "diff" in result:
      state["diff"] = result["diff"]
    state["project_tree"] = result["project_tree"]

    return state

  except ClonePathError as e:
    logger.error(f"[CLONE_PATH] ClonePathError: {e}")
    raise

  except DiffGenerationError as e:
    logger.error(f"[CLONE_PATH] DiffGenerationError: {e}")
    raise

  except Exception as e:
    logger.error(f"[CLONE_PATH] Error inesperado: {e}")
    raise ClonePathError(f"Error inesperado en nodo clone_path: {e}")
