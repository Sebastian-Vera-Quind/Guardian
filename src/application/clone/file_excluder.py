import os
from typing import List

try:
  import pathspec
except ImportError:
  pathspec = None


class FileExcluder:
  """
  Servicio que determina qué archivos incluir/excluir en diff y tree.
  Filtra según extensiones hardcoded y patrones .aiignore.
  """

  EXCLUDED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg",
    ".mp4", ".avi", ".mkv", ".mov",
    ".md"
  }

  EXCLUDED_NAMES = {
    "package-lock.json", "yarn.lock", "Pipfile.lock",
    "poetry.lock", "Gemfile.lock", "go.sum", "Cargo.lock"
  }

  def __init__(self, repo_path: str):
    """
    Inicializa FileExcluder y carga patrones .aiignore si existen.

    Args:
      repo_path: Ruta absoluta al repositorio
    """
    self.repo_path = repo_path
    self.aiignore_patterns = self._load_aiignore(repo_path)

  def _load_aiignore(self, repo_path: str) -> List[str]:
    """
    Parsea .aiignore si existe (formato gitignore estándar).

    Args:
      repo_path: Ruta absoluta al repositorio

    Returns:
      Lista de patrones (strings), vacía si no existe .aiignore
    """
    aiignore_path = os.path.join(repo_path, ".aiignore")
    if not os.path.exists(aiignore_path):
      return []

    patterns = []
    try:
      with open(aiignore_path, encoding="utf-8") as f:
        for line in f:
          line = line.strip()
          if line and not line.startswith("#"):
            patterns.append(line)
    except Exception:
      return []

    return patterns

  def should_include(self, file_path: str) -> bool:
    """
    Determina si un archivo debe incluirse en diff y tree.

    Args:
      file_path: Ruta absoluta o relativa del archivo

    Returns:
      True si debe incluirse, False si debe excluirse
    """
    name = os.path.basename(file_path)
    ext = os.path.splitext(name)[1].lower()

    if ext in self.EXCLUDED_EXTENSIONS:
      return False

    if name in self.EXCLUDED_NAMES:
      return False

    if name.endswith(".lock"):
      return False

    if pathspec:
      for pattern in self.aiignore_patterns:
        if self._matches_gitignore_pattern(file_path, pattern):
          return False

    return True

  @staticmethod
  def _matches_gitignore_pattern(file_path: str, pattern: str) -> bool:
    """
    Implementa matching gitignore estándar usando pathspec.

    Args:
      file_path: Ruta del archivo
      pattern: Patrón gitignore

    Returns:
      True si el archivo coincide con el patrón
    """
    if not pathspec:
      return False

    try:
      spec = pathspec.PathSpec.from_lines("gitwildmatch", [pattern])
      return spec.match_file(file_path)
    except Exception:
      return False
