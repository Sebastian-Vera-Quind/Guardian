import logging
from typing import Any, Dict, Optional, Set

from src.domain.ports.input import CloneService as CloneServicePort
from src.domain.ports.output import RepositoryCloner
from src.domain.models import ClonePathError, DiffGenerationError, DiffFile, ChangeType

from .file_excluder import FileExcluder
from .tree_builder import TreeBuilder

logger = logging.getLogger(__name__)


class CloneService(CloneServicePort):
  """
  Implementación de CloneService que orquesta clonación, checkout,
  generación de diff y construcción del árbol del proyecto.
  """

  def __init__(
    self,
    repository_cloner: RepositoryCloner,
  ):
    """
    Inicializa CloneService con dependencias inyectadas.

    Args:
      repository_cloner: Puerto RepositoryCloner
      diff_generator: Puerto DiffGenerator
    """
    self.repository_cloner = repository_cloner

  def clone(
    self,
    repo_url: str,
    installation_token: Optional[str] = None,
    commit_sha: Optional[str] = None,
    target: Optional[str] = None
  ) -> Dict[str, Any]:
    """
    Orquesta clonación, checkout, diff y tree del repositorio.

    Args:
      repo_url: URL del repositorio
      installation_token: Token GitHub App (opcional)
      commit_sha: SHA del commit donde hacer checkout
      target: SHA/rama de comparación para diff (opcional)

    Returns:
      Diccionario con clone_path, diff, modified_lines, project_tree

    Raises:
      ClonePathError: Si clonación o checkout fallan
      DiffGenerationError: Si generación de diff falla
    """
    result = {}

    try:
      logger.info(f"Clonando repositorio: {repo_url}")
      clone_path = self.repository_cloner.clone(repo_url, installation_token)
      result["clone_path"] = clone_path

      if commit_sha:
        self.repository_cloner.checkout(clone_path, commit_sha)

      file_excluder = FileExcluder(clone_path)

      diff: Dict[str, DiffFile] = {}
      added_files: Set[str] = set()
      modified_files: Set[str] = set()

      if target:
        def diff_callback(file_path: str, diff_file: DiffFile):
          diff[file_path] = diff_file
          if diff_file["is_new"]:
            added_files.add(file_path)
            return
          if not diff_file["is_deleted"]:
            # Un archivo modificado es aquel que no es nuevo y no fue eliminado
            modified_files.add(file_path)

        self.repository_cloner.get_diff(
          base_commit=commit_sha,
          target_commit=target,
          repo_path=clone_path,
          callback=diff_callback
        )
        result["diff"] = diff

      project_tree = TreeBuilder.build_tree(
        clone_path,
        file_excluder,
        added_files_set=added_files if added_files else None,
        modified_files_set=modified_files if modified_files else None
      )
      result["project_tree"] = project_tree
      logger.info(f"Árbol del proyecto construido")

      return result

    except ClonePathError:
      raise
    except DiffGenerationError:
      raise
    except Exception as e:
      logger.error(f"Error durante clonación: {e}")
      raise ClonePathError(f"Error durante clonación del repositorio: {e}")
