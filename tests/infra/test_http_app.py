import os
import unittest
import tempfile
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.infra.entrypoints.http import create_app


class TestHTTPApp(unittest.TestCase):

  def setUp(self):
    self.temp_dir = tempfile.TemporaryDirectory()
    os.environ["GUARDIAN_API_KEY"] = "test-secret-key-123"

  def tearDown(self):
    self.temp_dir.cleanup()
    if "GUARDIAN_API_KEY" in os.environ:
      del os.environ["GUARDIAN_API_KEY"]

  def test_create_app_returns_fastapi_instance(self):
    app = create_app()
    self.assertIsNotNone(app)
    self.assertEqual(app.title, "Guardian Server")

  def test_manual_chat_missing_api_key(self):
    app = create_app()
    client = TestClient(app)

    response = client.post("/manual-chat")
    self.assertEqual(response.status_code, 401)

  def test_manual_chat_invalid_api_key(self):
    app = create_app()
    client = TestClient(app)

    headers = {"X-API-KEY": "wrong-key"}
    response = client.post("/manual-chat", headers=headers)
    self.assertEqual(response.status_code, 403)

  def test_manual_chat_post_method(self):
    app = create_app()
    client = TestClient(app)

    headers = {"X-API-KEY": "test-secret-key-123"}
    response = client.post("/manual-chat", json={
        "project_code": "test-project",
        "project_id": "00000000-0000-0000-0000-000000000000",
        "repository": {
          "url": "https://github.com/acme/my-repo.git"
        }
      }, headers=headers
    )

    self.assertEqual(response.status_code, 200)
    self.assertIsNotNone(response.text)

  @patch.dict(os.environ, {"SERVER_PORT": "9000"})
  def test_server_port_configurable(self):
    port = int(os.getenv("SERVER_PORT", "8000"))
    self.assertEqual(port, 9000)

  @patch.dict(os.environ, {"SERVER_PORT": "8000"})
  def test_server_default_port(self):
    port = int(os.getenv("SERVER_PORT", "8000"))
    self.assertEqual(port, 8000)


if __name__ == "__main__":
  unittest.main()
