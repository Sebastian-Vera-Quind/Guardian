from abc import ABC, abstractmethod
from typing import List


class VectorSearchRepository(ABC):
  """Output port for pgvector architecture document search."""

  @abstractmethod
  def search_similar_chunks(
    self,
    project_code: str,
    query_text: str,
  ) -> List[str]:
    """Return architecture doc chunks similar to the query text.

    Args:
      project_code: Project code used to filter embeddings.
      query_text: Free-text query used to build the embedding.

    Returns:
      List of text chunks ordered by cosine similarity.
    """
    ...
