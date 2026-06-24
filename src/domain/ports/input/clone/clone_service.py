from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class CloneService(ABC):
  """
  Puerto de entrada que define contrato para orquestación de clonación,
  checkout, generación de diff y construcción del árbol del proyecto.
  """

  @abstractmethod
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
      Diccionario con:
      {
          "clone_path": str (ruta absoluta),
          "diff": List[Dict] (si target está presente),
          "modified_lines": int (si target está presente),
          "project_tree": Dict[str, Any],
          "added_files": set[str] (si target está presente)
      }

    Raises:
      ClonePathError: Si clonación o checkout fallan
      DiffGenerationError: Si generación de diff falla
      AgenticError: Otros errores
    """
    ...
