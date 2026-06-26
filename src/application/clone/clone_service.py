import logging
from typing import Any, Dict, List, Optional, Set

from src.domain.ports.input import CloneService as CloneServicePort
from src.domain.ports.output import RepositoryCloner
from src.domain.models import ClonePathError, DiffGenerationError, DiffFile

from .file_excluder import FileExcluder
from .tree_builder import TreeBuilder
from .file_replacer import FileReplacer

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
    """
    self.repository_cloner = repository_cloner

  def clone_repository(
    self,
    repo_url: str,
    installation_token: Optional[str] = None
  ) -> str:
    """
    Clona repositorio en /tmp/guardian/<uuid>, retorna ruta absoluta.

    Args:
      repo_url: URL del repositorio
      installation_token: Token GitHub App para autenticación (opcional)

    Returns:
      Ruta absoluta al directorio clonado

    Raises:
      ClonePathError: Si clonación falla
    """
    try:
      logger.info(f"Clonando repositorio: {repo_url}")
      clone_path = self.repository_cloner.clone(repo_url, installation_token)
      logger.info(f"Clonación exitosa: {clone_path}")
      return clone_path
    except ClonePathError:
      raise
    except Exception as e:
      logger.error(f"Error durante clonación: {e}")
      raise ClonePathError(f"Error durante clonación del repositorio: {e}")

  def checkout_commit(
    self,
    repo_path: str,
    commit_sha: str
  ) -> None:
    """
    Hace checkout a commit específico.

    Args:
      repo_path: Ruta absoluta al repositorio clonado
      commit_sha: SHA del commit a hacer checkout

    Raises:
      CheckoutError: Si el commit no existe o checkout falla
    """
    try:
      logger.info(f"Haciendo checkout a {commit_sha}")
      self.repository_cloner.checkout(repo_path, commit_sha)
      logger.info(f"Checkout exitoso: {commit_sha}")
    except Exception as e:
      logger.error(f"Error durante checkout: {e}")
      raise

  def replace_files_content(
    self,
    repo_path: str,
    files_content: List[Dict[str, str]]
  ) -> Set[str]:
    """
    Reemplaza contenido de archivos, creando si no existen.
    Preserva estructura de directorios.

    Args:
      repo_path: Ruta absoluta al repositorio clonado
      files_content: Lista de dicts con 'path' y 'content'

    Returns:
      Set de rutas relativas de archivos reemplazados/creados

    Raises:
      ClonePathError: Si falla el reemplazo
    """
    try:
      logger.info(f"Reemplazando {len(files_content)} archivos")
      modified_files = FileReplacer.replace_files(repo_path, files_content)
      logger.info(f"Archivos reemplazados: {len(modified_files)}")
      return modified_files
    except Exception as e:
      logger.error(f"Error durante reemplazo de archivos: {e}")
      raise ClonePathError(f"Error durante reemplazo de archivos: {e}")

  def generate_diff_and_tree(
    self,
    repo_path: str,
    base_commit: Optional[str],
    target_commit: Optional[str],
    files_modified_by_replacement: Optional[Set[str]] = None
  ) -> Dict[str, Any]:
    """
    Genera diff, project_tree, y métricas de cambios.

    Args:
      repo_path: Ruta absoluta al repositorio clonado
      base_commit: SHA del commit base (puede ser None para HEAD)
      target_commit: SHA/rama de comparación (puede ser None)
      files_modified_by_replacement: Set de archivos reemplazados

    Returns:
      Diccionario con diff, project_tree, modified_lines, added_files

    Raises:
      DiffGenerationError: Si generación de diff falla
    """
    try:
      file_excluder = FileExcluder(repo_path)

      diff: Dict[str, DiffFile] = {}
      added_files: Set[str] = set()
      modified_files: Set[str] = set()

      # Generar diff si hay target_commit O si hay archivos reemplazados.
      # Cuando target_commit es None pero hay archivos reemplazados,
      # se compara base_commit contra el working directory.
      if target_commit or files_modified_by_replacement:
        def diff_callback(file_path: str, diff_file: DiffFile):
          diff[file_path] = diff_file
          if diff_file["is_new"]:
            added_files.add(file_path)
            return
          if not diff_file["is_deleted"]:
            modified_files.add(file_path)

        self.repository_cloner.get_diff(
          base_commit=base_commit,
          target_commit=target_commit,
          repo_path=repo_path,
          callback=diff_callback
        )

      # Agregar archivos reemplazados al set de modificados
      if files_modified_by_replacement:
        modified_files.update(files_modified_by_replacement)

      project_tree = TreeBuilder.build_tree(
        repo_path,
        file_excluder,
        added_files_set=added_files if added_files else None,
        modified_files_set=modified_files if modified_files else None
      )

      result: Dict[str, Any] = {
        "project_tree": project_tree,
        "added_files": added_files
      }

      if diff:
        result["diff"] = diff

      return result

    except DiffGenerationError:
      raise
    except Exception as e:
      logger.error(f"Error durante generación de diff: {e}")
      raise DiffGenerationError(f"Error durante generación de diff: {e}")
