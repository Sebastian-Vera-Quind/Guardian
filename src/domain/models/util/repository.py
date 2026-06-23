from typing import Optional
from datetime import datetime
from typing_extensions import TypedDict


class RepositoryMetadata(TypedDict):
  owner: str
  repo_name: str
  branch: str = "main"
  commit_sha: Optional[str] = None
  author_name: str = "Unknown Author"
  author_email: Optional[str] = None
  commit_message: Optional[str] = None
  timestamp: Optional[datetime] = None

class RepositoryInput(TypedDict):
  """Entrada para información del repositorio."""
  url: str  
  installation: Optional[str] = None
  commit_sha: str
  target: str