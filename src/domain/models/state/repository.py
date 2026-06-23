from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class RepositoryMetadata(BaseModel):
    owner: str
    repo_name: str
    branch: str = "main"
    commit_sha: Optional[str] = None
    author_name: str = "Unknown Author"
    author_email: Optional[str] = None
    commit_message: Optional[str] = None
    timestamp: Optional[datetime] = None
