from __future__ import annotations

from enum import Enum
from typing import NotRequired
from typing_extensions import TypedDict

class TreeObjectType(str, Enum):
  FILE = "file"
  DIRECTORY = "directory"
  
class TreeObject(TypedDict):
  name: str
  type: TreeObjectType
  is_new: NotRequired[bool]
  children: NotRequired[list["TreeObject"]]