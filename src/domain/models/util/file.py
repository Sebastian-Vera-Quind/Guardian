from pydantic import BaseModel, ConfigDict


class FileContent(BaseModel):
  model_config = ConfigDict(extra="forbid")

  path: str
  content: str
  extension: str

  def __getitem__(self, key: str):
    """Support dictionary-style subscript access for backwards compatibility."""
    return getattr(self, key)
