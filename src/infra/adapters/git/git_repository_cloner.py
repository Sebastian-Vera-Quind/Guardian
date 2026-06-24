import logging
import os
import re
from uuid import uuid4
from collections import Counter
from typing import Callable, Optional, List

from git import Repo
from git.exc import GitCommandError

from src.domain.ports.output import RepositoryCloner
from src.domain.models import ClonePathError, CheckoutError, DiffFile, DiffContent, ChangeType, DiffGenerationError

logger = logging.getLogger(__name__)

CLONE_BASE_DIR = "/tmp/guardian"
HUNK_RE = re.compile(b"^@@ -(\\d+),?\\d* \\+(\\d+),?\\d* @@")

class GitRepositoryCloner(RepositoryCloner):
  """
  Implementación de RepositoryCloner usando GitPython.
  Clona en /tmp/guardian/<uuid v4>/ con autenticación opcional.
  """

  def __init__(self):
    """Inicializa GitRepositoryCloner."""
    if not os.path.exists(CLONE_BASE_DIR):
      os.makedirs(CLONE_BASE_DIR, exist_ok=True)

  def clone(
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
      ClonePathError: Si la clonación falla
    """
    clone_path = os.path.join(CLONE_BASE_DIR, str(uuid4()))

    auth_url = self._build_clone_url(repo_url, installation_token)

    try:
      logger.info(f"Clonando {repo_url} en {clone_path}")
      os.makedirs(clone_path, exist_ok=True)
      Repo.clone_from(auth_url, clone_path)
      logger.info(f"Clonación exitosa: {clone_path}")
      return clone_path

    except GitCommandError as e:
      logger.error(f"Error de git durante clonación: {e}")
      self._cleanup_dir(clone_path)
      raise ClonePathError(f"Falló la clonación del repositorio: {e}")

    except Exception as e:
      logger.error(f"Error inesperado durante clonación: {e}")
      self._cleanup_dir(clone_path)
      raise ClonePathError(f"Error inesperado durante clonación: {e}")

  def checkout(self, repo_path: str, commit_sha: str) -> None:
    """
    Hace checkout a commit específico.

    Args:
      repo_path: Ruta absoluta al repositorio clonado
      commit_sha: SHA del commit a hacer checkout

    Raises:
      CheckoutError: Si el commit no existe o checkout falla
    """
    try:
      logger.info(f"Haciendo checkout a {commit_sha} en {repo_path}")
      repo = Repo(repo_path)
      repo.git.checkout(commit_sha)
      logger.info(f"Checkout exitoso: {commit_sha}")

    except GitCommandError as e:
      logger.error(f"Error de git durante checkout: {e}")
      raise CheckoutError(f"Falló el checkout a {commit_sha}: {e}")

    except Exception as e:
      logger.error(f"Error inesperado durante checkout: {e}")
      raise CheckoutError(f"Error inesperado durante checkout: {e}")

  @staticmethod
  def _build_clone_url(url: str, installation_token: Optional[str]) -> str:
    """
    Construye URL para clonación con autenticación opcional.

    Args:
      url: URL original del repositorio
      installation_token: Token GitHub App

    Returns:
      URL con autenticación incrustada si token está presente
    """
    if not installation_token:
      return url

    return url.replace(
      "https://github.com/",
      f"https://x-access-token:{installation_token}@github.com/"
    )

  @staticmethod
  def _cleanup_dir(path: str) -> None:
    """
    Limpia directorio en caso de error.

    Args:
      path: Ruta del directorio a limpiar
    """
    try:
      import shutil
      if os.path.exists(path):
        shutil.rmtree(path)
        logger.info(f"Directorio limpiado: {path}")
    except Exception as e:
      logger.warning(f"No se pudo limpiar {path}: {e}")

  def get_diff(
    self,
    repo_path: str,
    target_commit: str,
    callback: Callable[[str, DiffFile], None],
    base_commit: Optional[str] = None, 
  ) -> None:
    try:
      repo = Repo(repo_path)
      base = repo.commit(base_commit) if base_commit else repo.head.commit
      target = repo.commit(target_commit)
      changes = target.diff(base, create_patch=True)
     
      for diff in changes.iter_change_type('M'):
        file_path = diff.b_path
        splits = diff.diff.splitlines()
        
        modified_lines: List[DiffContent] = []
        deleted_line_number = 0
        added_line_number = 0
        content_lines = Counter[str]()
      
        for line in splits:
          if line.startswith(b'@@'):
            match = HUNK_RE.match(line)
            if match:
              deleted_line_number = int(match.group(1))
              added_line_number = int(match.group(2))
            continue
          
          if deleted_line_number == 0 and added_line_number == 0:
            continue
          
          if line.startswith(b'-') and not line.startswith(b'---'):
            modified_lines.append(DiffContent(
              content=line[1:].decode('utf-8', errors='ignore'),
              status=ChangeType.DELETED,
              line_number=deleted_line_number
            ))
            deleted_line_number += 1
            content_lines["deletions"] += 1
          elif line.startswith(b'+') and not line.startswith(b'+++'):
            modified_lines.append(DiffContent(
              content=line[1:].decode('utf-8', errors='ignore'),
              status=ChangeType.ADDED,
              line_number=added_line_number
            ))
            added_line_number += 1
            content_lines["additions"] += 1 
          
          else:
            deleted_line_number += 1
            added_line_number += 1
        callback(file_path, DiffFile(
          content=modified_lines,
          additions=content_lines["additions"],
          deletions=content_lines["deletions"],
          is_deleted=False,
          is_new=False
        ))
        
      for diff in changes.iter_change_type('D'):
        file_path = diff.a_path
        callback(file_path, DiffFile(
          content=[],
          additions=0,
          deletions=0,
          is_deleted=True,
          is_new=False
        ))
      
      for diff in changes.iter_change_type('A'):
        file_path = diff.b_path
        added_line_number = 0
        added_lines = 0
        modified_lines: List[DiffContent] = []
        
        for line in diff.diff.splitlines():
          if line.startswith(b'@@'):
            match = HUNK_RE.match(line)
            if match:
              added_line_number = int(match.group(2))
            continue
          
          if added_line_number == 0:
            continue
          
          if line.startswith(b'+') and not line.startswith(b'+++'):
            modified_lines.append(DiffContent(
              content=line[1:].decode('utf-8', errors='ignore'),
              status=ChangeType.ADDED,
              line_number=added_line_number
            ))
            added_line_number += 1
            added_lines += 1
        
        callback(file_path, DiffFile(
          content=modified_lines,
          additions=added_lines,
          deletions=0,
          is_deleted=False,
          is_new=True
        ))
      
    except Exception as e:
      raise DiffGenerationError(f"Falló la generación del diff: {e}")
