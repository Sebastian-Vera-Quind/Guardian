from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set


class CloneService(ABC):
  """
  Puerto de entrada que define contrato para orquestación de clonación,
  checkout, generación de diff y construcción del árbol del proyecto.
  """

  @abstractmethod
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
    ...

  @abstractmethod
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
    ...

  @abstractmethod
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
    ...

  @abstractmethod
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
      Diccionario con:
      {
          "diff": Dict[str, DiffFile],
          "project_tree": TreeObject,
          "modified_lines": int,
          "added_files": Set[str]
      }

    Raises:
      DiffGenerationError: Si generación de diff falla
    """
    ...
