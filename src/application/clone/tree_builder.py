import os
from typing import Optional, Set

from .file_excluder import FileExcluder
from src.domain.models import TreeObject, TreeObjectType


class TreeBuilder:
  """
  Servicio que construye árbol jerárquico del repositorio.
  Respeta FileExcluder y marca archivos nuevos según diff.
  """

  @staticmethod
  def build_tree(
    repo_path: str,
    file_excluder: FileExcluder,
    added_files_set: Optional[Set[str]] = None,
    modified_files_set: Optional[Set[str]] = None
  ) -> TreeObject:
    """
    Construye árbol jerárquico del repositorio respetando exclusiones.

    Args:
      repo_path: Ruta absoluta al repositorio
      file_excluder: Instancia de FileExcluder
      added_files_set: Set de rutas de archivos nuevos (para marcar is_new)
      modified_files_set: Set de rutas de archivos modificados (para marcar is_modified)

    Returns:
      Dict con estructura jerárquica:
      {
          "name": str,
          "type": "directory" | "file",
          "children": [...] (opcional, solo si es directorio),
          "is_new": bool (opcional, solo si es archivo nuevo),
          "is_modified": bool (opcional, solo si el archivo fue modificado)
      }
    """
    if added_files_set is None:
      added_files_set = set()
    if modified_files_set is None:
      modified_files_set = set()

    def _traverse(path: str) -> TreeObject:
      """Recorre recursivamente el árbol."""
      name = os.path.basename(path) or "root"
      is_dir = os.path.isdir(path)

      node: TreeObject = {
        "name": name,
        "type": TreeObjectType.DIRECTORY if is_dir else TreeObjectType.FILE
      }

      if is_dir:
        children: list[TreeObject] = []
        try:
          entries = os.listdir(path)
        except (PermissionError, OSError):
          entries = []

        for entry in entries:
          entry_path = os.path.join(path, entry)

          if not file_excluder.should_include(entry_path):
            continue

          try:
            child = _traverse(entry_path)
            children.append(child)
          except (PermissionError, OSError):
            continue

        if children:
          node["children"] = children

      else:
        # Convertir ruta absoluta a relativa para comparación con los sets
        relative_path = os.path.relpath(path, repo_path)
        if relative_path in added_files_set:
          node["is_new"] = True
        if relative_path in modified_files_set:
          node["is_modified"] = True

      return node

    return _traverse(repo_path)
