import math
import unittest
from unittest.mock import MagicMock, patch


class TestLiteLLMProvider(unittest.TestCase):

  def _make_embedding_response(self, values):
    embedding_obj = MagicMock()
    embedding_obj.embedding = values
    data_item = MagicMock()
    data_item.__getitem__ = lambda self, idx: embedding_obj
    response = MagicMock()
    response.data = [embedding_obj]
    return response

  @patch("src.infra.adapters.ai.litellm_provider.OpenAI")
  def test_embed_returns_float_list(self, mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    mock_client.embeddings.create.return_value = (
      self._make_embedding_response([0.1, 0.2, 0.3])
    )

    from src.infra.adapters.ai.litellm_provider import LiteLLMProvider
    provider = LiteLLMProvider()
    result = provider.embed("hello world")

    self.assertEqual(result, [0.1, 0.2, 0.3])
    self.assertIsInstance(result, list)

  @patch("src.infra.adapters.ai.litellm_provider.OpenAI")
  def test_embed_filters_nan_inf(self, mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    raw = [0.1, float("nan"), float("inf"), 0.3, float("-inf")]
    mock_client.embeddings.create.return_value = (
      self._make_embedding_response(raw)
    )

    from src.infra.adapters.ai.litellm_provider import LiteLLMProvider
    provider = LiteLLMProvider()
    result = provider.embed("test text")

    for v in result:
      self.assertFalse(math.isnan(v), f"NaN found in result: {result}")
      self.assertFalse(math.isinf(v), f"Inf found in result: {result}")
    self.assertIn(0.1, result)
    self.assertIn(0.3, result)


if __name__ == "__main__":
  unittest.main()
