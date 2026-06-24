from enum import Enum
from typing import List
from typing_extensions import TypedDict

class ChangeType(Enum):
  ADDED = "added"
  DELETED = "deleted"

class DiffContent(TypedDict):
  content: str
  line_number: int
  status: ChangeType

class DiffFile(TypedDict):
  is_new: bool
  is_deleted: bool
  additions: int
  deletions: int
  content: List[DiffContent]
  