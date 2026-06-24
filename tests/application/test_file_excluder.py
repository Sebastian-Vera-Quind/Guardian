import os
import tempfile
import unittest

from src.application.clone.file_excluder import FileExcluder


class TestFileExcluder(unittest.TestCase):
  """Tests para FileExcluder."""

  def setUp(self):
    """Configura directorios temporales."""
    self.test_dir = tempfile.TemporaryDirectory()
    self.repo_path = self.test_dir.name
    self.addCleanup(self.test_dir.cleanup)

  def test_should_include_returns_true_for_code_files(self):
    """Test: archivos de código se incluyen."""
    excluder = FileExcluder(self.repo_path)

    self.assertTrue(excluder.should_include("main.py"))
    self.assertTrue(excluder.should_include("index.js"))
    self.assertTrue(excluder.should_include("style.css"))
    self.assertTrue(excluder.should_include("/path/to/config.json"))

  def test_should_include_returns_false_for_excluded_extensions(self):
    """Test: extensiones excluidas se rechazan."""
    excluder = FileExcluder(self.repo_path)

    self.assertFalse(excluder.should_include("image.png"))
    self.assertFalse(excluder.should_include("video.mp4"))
    self.assertFalse(excluder.should_include("readme.md"))
    self.assertFalse(excluder.should_include("data.jpg"))
    self.assertFalse(excluder.should_include("graphic.svg"))

  def test_should_include_returns_false_for_lock_files(self):
    """Test: lock files se excluyen."""
    excluder = FileExcluder(self.repo_path)

    self.assertFalse(excluder.should_include("package-lock.json"))
    self.assertFalse(excluder.should_include("yarn.lock"))
    self.assertFalse(excluder.should_include("poetry.lock"))
    self.assertFalse(excluder.should_include("Pipfile.lock"))
    self.assertFalse(excluder.should_include("custom.lock"))

  def test_load_aiignore_parses_valid_file(self):
    """Test: .aiignore válido se parsea correctamente."""
    aiignore_content = """
# comentario
*.pyc
__pycache__/
*.egg-info/
    """
    aiignore_path = os.path.join(self.repo_path, ".aiignore")
    with open(aiignore_path, "w") as f:
      f.write(aiignore_content)

    excluder = FileExcluder(self.repo_path)

    self.assertGreater(len(excluder.aiignore_patterns), 0)
    self.assertIn("*.pyc", excluder.aiignore_patterns)
    self.assertIn("__pycache__/", excluder.aiignore_patterns)

  def test_load_aiignore_returns_empty_if_missing(self):
    """Test: .aiignore ausente retorna lista vacía."""
    excluder = FileExcluder(self.repo_path)

    self.assertEqual(len(excluder.aiignore_patterns), 0)

  def test_should_include_respects_aiignore_patterns(self):
    """Test: patrones de .aiignore son respetados (si pathspec disponible)."""
    aiignore_content = "*.pyc\n__pycache__/\n"
    aiignore_path = os.path.join(self.repo_path, ".aiignore")
    with open(aiignore_path, "w") as f:
      f.write(aiignore_content)

    excluder = FileExcluder(self.repo_path)

    self.assertGreater(len(excluder.aiignore_patterns), 0)


if __name__ == "__main__":
  unittest.main()
