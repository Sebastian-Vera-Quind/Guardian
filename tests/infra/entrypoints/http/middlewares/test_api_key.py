import os
import unittest
from unittest.mock import MagicMock

from src.infra.entrypoints.http.middlewares.api_key import validate_api_key
from src.infra.entrypoints.http.errors import APIKeyMissingError, APIKeyInvalidError


def _make_request(api_key=None):
  """Returns a mock Request with X-API-KEY header set to api_key (or absent if None)."""
  request = MagicMock()
  request.headers.get = lambda key, default=None: (
    api_key if (key == "X-API-KEY" and api_key is not None) else default
  )
  return request


class TestApiKeyMiddleware(unittest.IsolatedAsyncioTestCase):
  """Unit tests for validate_api_key dependency — no HTTP layer involved."""

  def setUp(self):
    os.environ["GUARDIAN_API_KEY"] = "test-secret-key-123"

  def tearDown(self):
    os.environ.pop("GUARDIAN_API_KEY", None)

  async def test_missing_header_raises_api_key_missing_error(self):
    """No X-API-KEY header → APIKeyMissingError."""
    request = _make_request(api_key=None)
    with self.assertRaises(APIKeyMissingError):
      await validate_api_key(request)

  async def test_wrong_key_raises_api_key_invalid_error(self):
    """Wrong X-API-KEY value → APIKeyInvalidError."""
    request = _make_request(api_key="wrong-key")
    with self.assertRaises(APIKeyInvalidError):
      await validate_api_key(request)

  async def test_correct_key_does_not_raise(self):
    """Correct X-API-KEY → no exception raised."""
    request = _make_request(api_key="test-secret-key-123")
    await validate_api_key(request)  # must not raise


if __name__ == "__main__":
  unittest.main()
