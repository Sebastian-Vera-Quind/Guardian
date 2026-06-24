from typing import Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from pydantic import BaseModel, ConfigDict


@dataclass
class RepositoryMetadata(dict):
  owner: str
  repo_name: str
  branch: str = "main"
  commit_sha: Optional[str] = None
  author_name: str = "Unknown Author"
  author_email: Optional[str] = None
  commit_message: Optional[str] = None
  timestamp: Optional[datetime] = None

  def __post_init__(self):
    """Initialize dict with dataclass fields."""
    super().__init__(asdict(self))

  def __getitem__(self, key: str):
    """Support dictionary-style subscript access."""
    return getattr(self, key)

class RepositoryInput(BaseModel):
  """Entrada para información del repositorio."""
  model_config = ConfigDict(extra="forbid")

  url: str
  installation: Optional[str] = None
  commit_sha: Optional[str] = None
  target: Optional[str] = None
  branch: Optional[str] = None

  def __getitem__(self, key: str):
    """Support dictionary-style subscript access for backwards compatibility."""
    return getattr(self, key, None)