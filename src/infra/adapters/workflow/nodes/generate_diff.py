import logging

from src.domain.models import AgentState, DiffGenerationError
from src.infra.adapters.workflow.log import with_logging
from src.infra.helper import inject, InPortType

logger = logging.getLogger(__name__)


@with_logging()
async def node_generate_diff(state: AgentState) -> AgentState:
  """
  Nodo independiente para generación de diff y project_tree.

  Responsabilidades:
    1. Extraer clone_path, commit_sha (opcional) y target (opcional)
    2. Determinar commits base y target para comparación
    3. Generar diff, project_tree y métricas
    4. Escribir en estado: diff, project_tree, modified_lines

  Args:
    state: AgentState con clone_path, repository.commit_sha (opcional),
           repository.target (opcional), _replaced_files (opcional)

  Returns:
    AgentState con diff, project_tree, modified_lines

  Raises:
    DiffGenerationError: Si generación de diff falla
  """
  try:
    clone_path = state.get("clone_path")
    repository = state.get("repository", {})

    if not clone_path:
      logger.error("[GENERATE_DIFF] Falta clone_path")
      raise DiffGenerationError("Falta 'clone_path' en estado")

    commit_sha = (
      repository.get("commit_sha")
      if isinstance(repository, dict)
      else getattr(repository, "commit_sha", None)
    )
    target = (
      repository.get("target")
      if isinstance(repository, dict)
      else getattr(repository, "target", None)
    )

    # Archivos reemplazados en el nodo anterior (puede ser None)
    replaced_files = state.get("_replaced_files")

    logger.info(
      f"[GENERATE_DIFF] Parámetros: "
      f"base_commit={commit_sha}, target={target}, "
      f"has_replaced_files={bool(replaced_files)}"
    )

    clone_service = inject(InPortType.CloneService)
    result = clone_service.generate_diff_and_tree(
      repo_path=clone_path,
      base_commit=commit_sha,
      target_commit=target,
      files_modified_by_replacement=replaced_files
    )

    # Escribir resultados en estado
    if "diff" in result:
      state["diff"] = result["diff"]

    if "project_tree" in result:
      state["project_tree"] = result["project_tree"]

    # Calcular modified_lines como suma de additions + deletions
    if "diff" in result:
      modified_lines = sum(
        diff_file.get("additions", 0) + diff_file.get("deletions", 0)
        for diff_file in result["diff"].values()
      )
      state["modified_lines"] = modified_lines

    # Limpiar estado interno
    state.pop("_replaced_files", None)

    return state

  except DiffGenerationError as e:
    logger.error(f"[GENERATE_DIFF] DiffGenerationError: {e}")
    raise

  except Exception as e:
    logger.error(f"[GENERATE_DIFF] Error inesperado: {e}")
    raise DiffGenerationError(f"Error inesperado en nodo generate_diff: {e}")
