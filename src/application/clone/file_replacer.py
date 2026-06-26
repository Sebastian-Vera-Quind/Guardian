import logging
import os
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class FileReplacer:
  """
  Servicio que reemplaza contenido de archivos en un repositorio clonado.
  Crea archivos si no existen, preservando estructura de directorios.
  """

  @staticmethod
  def replace_files(
    repo_path: str,
    files_content: List[Dict[str, str]]
  ) -> Set[str]:
    """
    Reemplaza contenido de archivos en el repositorio.
    Crea directorios y archivos si no existen.

    Args:
      repo_path: Ruta absoluta al repositorio clonado
      files_content: Lista de dicts con 'path' y 'content'

    Returns:
      Set de rutas relativas de archivos reemplazados/creados

    Raises:
      OSError: Si falla la creación/escritura de archivos
    """
    modified_files: Set[str] = set()

    for file_obj in files_content:
      if isinstance(file_obj, dict):
        file_path = file_obj.get("path")
        content = file_obj.get("content")
      else:
        # Asumir que es un objeto con atributos
        file_path = getattr(file_obj, "path", None)
        content = getattr(file_obj, "content", None)

      if not file_path or content is None:
        logger.warning(
          f"Salteando archivo sin path o content: {file_obj}"
        )
        continue

      absolute_path = os.path.join(repo_path, file_path)

      # Normalizar ruta
      absolute_path = os.path.normpath(absolute_path)

      # Crear directorio padre si no existe
      directory = os.path.dirname(absolute_path)
      if directory and not os.path.exists(directory):
        try:
          os.makedirs(directory, exist_ok=True)
          logger.debug(f"Creado directorio: {directory}")
        except OSError as e:
          logger.error(f"Error creando directorio {directory}: {e}")
          raise

      # Escribir archivo
      try:
        with open(absolute_path, "w", encoding="utf-8") as f:
          f.write(content)
        logger.debug(f"Archivo reemplazado/creado: {file_path}")
        modified_files.add(file_path)
      except OSError as e:
        logger.error(f"Error escribiendo archivo {file_path}: {e}")
        raise

    return modified_files
