from typing import Dict, List, Union

from pydantic import BaseModel, ConfigDict
from typing_extensions import TypeAliasType

JsonValue = TypeAliasType(
  "JsonValue",
  Union[
    str,
    int,
    float,
    bool,
    None,
    List["JsonValue"],
    Dict[str, "JsonValue"],
  ],
)


class ProjectContext(BaseModel):
  """
  Entidad que representa el contexto de un proyecto.

  Contiene información sobre reglas, estructura y configuración del proyecto.
  """

  model_config = ConfigDict(frozen=True)

  project_code: str
  scope: str
  data: Dict[str, "JsonValue"]
