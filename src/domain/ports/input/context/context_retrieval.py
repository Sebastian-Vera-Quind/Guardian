from abc import ABC, abstractmethod

from src.domain.models.retrieved_context import RetrievedContext


class ContextRetriever(ABC):
  """Input port (use case) for retrieving RAG context for a project."""

  @abstractmethod
  def retrieve(
    self,
    project_code: str,
    query_text: str,
    scope: str = "review",
  ) -> RetrievedContext:
    """Retrieve rules, architecture chunks, coding standards and
    project fields for the given project.

    Args:
      project_code: Unique project identifier.
      query_text: Text used for semantic similarity search.
      scope: Rules scope passed to RulesRepository. Default: "review".

    Returns:
      RetrievedContext populated with all available context.
    """
    ...
