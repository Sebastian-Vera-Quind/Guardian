import logging
import math
import os
from typing import List

from openai import OpenAI

from src.domain.models import JsonValue
from src.domain.ports.output import AIProvider

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-004")


class LiteLLMProvider(AIProvider):
  """AIProvider adapter backed by a LiteLLM proxy (OpenAI-compatible).

  Reads connection config from environment variables:
    - LITELLM_BASE_URL  (default: http://localhost:4000)
    - LITELLM_API_KEY   (default: dummy)
  """

  def __init__(self) -> None:
    base_url = os.getenv(
      "LITELLM_BASE_URL", "http://localhost:4000"
    )
    api_key = os.getenv("LITELLM_API_KEY", "dummy")
    self._client = OpenAI(base_url=base_url, api_key=api_key)

  def embed(self, text: str) -> List[float]:
    """Generate an embedding vector, filtering NaN and Inf values.

    Args:
      text: Text to embed.

    Returns:
      List of finite float values.
    """
    response = self._client.embeddings.create(
      model=_EMBEDDING_MODEL,
      input=text,
    )
    raw: List[float] = response.data[0].embedding
    cleaned = [
      v for v in raw
      if not (math.isnan(v) or math.isinf(v))
    ]
    logger.info(
      "embed model=%s input_len=%d vector_len=%d",
      _EMBEDDING_MODEL,
      len(text),
      len(cleaned),
    )
    return cleaned

  def complete(self, prompt: str, **opts: JsonValue) -> str:
    """Text completion via the LiteLLM proxy.

    Args:
      prompt: System + user combined prompt string.
      **opts: Additional options forwarded to the completion call.

    Returns:
      Generated text content.
    """
    raise NotImplementedError(
      "LiteLLMProvider.complete is not yet implemented"
    )
