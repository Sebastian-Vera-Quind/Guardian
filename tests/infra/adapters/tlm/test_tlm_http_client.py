import os
import unittest
from unittest.mock import MagicMock, patch


class TestTlmHttpClient(unittest.TestCase):

  def _make_client(self, base_url="http://tlm.test"):
    with patch.dict(os.environ, {"TLM_BASE_URL": base_url}):
      from src.infra.adapters.tlm.tlm_http_client import TlmHttpClient
      return TlmHttpClient()

  def test_get_project_by_code_returns_dict_on_success(self):
    client = self._make_client()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
      "body": {"id": "uuid-1", "code": "PROJ"}
    }
    mock_response.raise_for_status = MagicMock()
    with patch("httpx.get", return_value=mock_response):
      result = client.get_project_by_code("PROJ")
    self.assertEqual(result, {"id": "uuid-1", "code": "PROJ"})

  def test_get_project_by_code_returns_none_when_base_url_empty(self):
    with patch.dict(os.environ, {"TLM_BASE_URL": ""}):
      from importlib import import_module, reload
      import src.infra.adapters.tlm.tlm_http_client as m
      reload(m)
      client = m.TlmHttpClient()
    result = client.get_project_by_code("PROJ")
    self.assertIsNone(result)

  def test_get_project_by_code_returns_none_on_http_error(self):
    client = self._make_client()
    with patch("httpx.get", side_effect=Exception("timeout")):
      result = client.get_project_by_code("PROJ")
    self.assertIsNone(result)

  def test_search_coding_standards_returns_list(self):
    client = self._make_client()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
      "body": [
        {"name": "PEP8", "description": "style guide"},
        {"name": "Typing", "description": "use type hints"},
      ]
    }
    mock_response.raise_for_status = MagicMock()
    with patch("httpx.get", return_value=mock_response):
      result = client.search_coding_standards("PROJ", "typing", 5)
    self.assertEqual(len(result), 2)
    self.assertEqual(result[0].name, "PEP8")

  def test_search_coding_standards_returns_empty_on_error(self):
    client = self._make_client()
    with patch("httpx.get", side_effect=Exception("network err")):
      result = client.search_coding_standards("PROJ", "query", 5)
    self.assertEqual(result, [])


if __name__ == "__main__":
  unittest.main()
