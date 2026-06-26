from abc import ABC, abstractmethod
from typing import Callable, Optional

from src.domain.models import DiffFile


class RepositoryCloner(ABC):
  """
  Puerto de salida que abstrae operaciones de clonación y checkout de
  repositorios.
  """

  @abstractmethod
  def clone(
    self,
    repo_url: str,
    installation_token: Optional[str] = None
  ) -> str:
    """
    Clona repositorio en /tmp/guardian/<uuid>, retorna ruta absoluta.

    Args:
      repo_url: URL del repositorio (p. ej. https://github.com/user/repo)
      installation_token: Token GitHub App para autenticación (opcional)

    Returns:
      Ruta absoluta al directorio clonado

    Raises:
      GitOperationError: Si la clonación falla (URL inválida, auth rechazada, etc.)
    """
    ...

  @abstractmethod
  def checkout(self, repo_path: str, commit_sha: str) -> None:
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
  def get_diff(
    self,
    repo_path: str,
    target_commit: Optional[str],
    callback: Callable[[str, DiffFile], None],
    base_commit: Optional[str] = None,
  ) -> None:
    """
    Genera diff línea por línea entre dos commits y llama a call_back
    para cada archivo modificado.

    Si target_commit es None, compara contra HEAD (working directory).
    """
    ...
