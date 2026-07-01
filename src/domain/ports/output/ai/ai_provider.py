from abc import ABC, abstractmethod
from typing import List

from src.domain.models.project_context import JsonValue


class AIProvider(ABC):
  """Output port for AI services (embeddings and completions)."""

  @abstractmethod
  def embed(self, text: str) -> List[float]:
    """Generate a vector embedding for the given text.

    Args:
      text: Input text to embed.

    Returns:
      List of floats representing the embedding vector.
    """
    ...

  @abstractmethod
  def complete(self, prompt: str, **opts: JsonValue) -> str:
    """Generate a text completion for the given prompt.

    Args:
      prompt: Instruction or context for the LLM.
      **opts: Additional options forwarded to the underlying model.

    Returns:
      Generated text string.
    """
    ...
