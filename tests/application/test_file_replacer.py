import os
import tempfile
import unittest

from src.application.clone.file_replacer import FileReplacer


class TestFileReplacer(unittest.TestCase):
  """Tests para el servicio FileReplacer."""

  def setUp(self):
    """Crear directorio temporal para tests."""
    self.temp_dir = tempfile.TemporaryDirectory()
    self.repo_path = self.temp_dir.name

  def tearDown(self):
    """Limpiar directorio temporal."""
    self.temp_dir.cleanup()

  def test_replace_files_creates_new_files(self):
    """T3: Crear archivos nuevos."""
    files_content = [
      {"path": "src/main.py", "content": "print('hello')"},
      {"path": "utils.py", "content": "def helper(): pass"}
    ]

    modified = FileReplacer.replace_files(self.repo_path, files_content)

    assert "src/main.py" in modified
    assert "utils.py" in modified
    assert len(modified) == 2

    # Verificar contenido
    with open(os.path.join(self.repo_path, "src/main.py")) as f:
      assert f.read() == "print('hello')"

  def test_replace_files_overwrites_existing_files(self):
    """T3: Sobrescribir archivos existentes."""
    # Crear archivo existente
    os.makedirs(os.path.join(self.repo_path, "src"), exist_ok=True)
    existing_file = os.path.join(self.repo_path, "src/main.py")
    with open(existing_file, "w") as f:
      f.write("old content")

    # Reemplazar
    files_content = [
      {"path": "src/main.py", "content": "new content"}
    ]

    modified = FileReplacer.replace_files(self.repo_path, files_content)

    assert "src/main.py" in modified
    with open(existing_file) as f:
      assert f.read() == "new content"

  def test_replace_files_preserves_directory_structure(self):
    """T3: Preservar estructura de directorios."""
    files_content = [
      {"path": "src/app/main.py", "content": "main"},
      {"path": "src/app/utils/helper.py", "content": "helper"}
    ]

    modified = FileReplacer.replace_files(self.repo_path, files_content)

    assert len(modified) == 2
    assert os.path.exists(os.path.join(self.repo_path, "src/app/main.py"))
    assert os.path.exists(os.path.join(
      self.repo_path, "src/app/utils/helper.py"
    ))

  def test_replace_files_empty_list_returns_empty_set(self):
    """T3: Lista vacía retorna set vacío."""
    modified = FileReplacer.replace_files(self.repo_path, [])

    assert modified == set()

  def test_replace_files_skips_missing_path(self):
    """T3: Saltar objeto sin path."""
    files_content = [
      {"path": "file1.py", "content": "content1"},
      {"content": "content2"},  # Falta path
      {"path": "file3.py", "content": "content3"}
    ]

    modified = FileReplacer.replace_files(self.repo_path, files_content)

    # Solo file1.py y file3.py deben ser creados
    assert "file1.py" in modified
    assert "file3.py" in modified
    assert len(modified) == 2

  def test_replace_files_skips_missing_content(self):
    """T3: Saltar objeto sin content."""
    files_content = [
      {"path": "file1.py", "content": "content1"},
      {"path": "file2.py"},  # Falta content
      {"path": "file3.py", "content": "content3"}
    ]

    modified = FileReplacer.replace_files(self.repo_path, files_content)

    # Solo file1.py y file3.py deben ser creados
    assert "file1.py" in modified
    assert "file3.py" in modified
    assert len(modified) == 2

  def test_replace_files_handles_nested_paths(self):
    """T3: Manejar rutas profundas."""
    files_content = [
      {
        "path": "very/deep/nested/structure/file.py",
        "content": "nested"
      }
    ]

    modified = FileReplacer.replace_files(self.repo_path, files_content)

    assert "very/deep/nested/structure/file.py" in modified
    full_path = os.path.join(
      self.repo_path, "very/deep/nested/structure/file.py"
    )
    assert os.path.exists(full_path)
    with open(full_path) as f:
      assert f.read() == "nested"

  def test_replace_files_returns_relative_paths(self):
    """T3: Retornar rutas relativas."""
    files_content = [
      {"path": "src/main.py", "content": "main"},
      {"path": "config.yaml", "content": "config"}
    ]

    modified = FileReplacer.replace_files(self.repo_path, files_content)

    # Las rutas retornadas deben ser relativas (sin /)
    for path in modified:
      assert not path.startswith("/")
      assert path in {"src/main.py", "config.yaml"}

  def test_replace_files_with_object_attributes(self):
    """T3: Soportar objetos con atributos."""
    class FileObj:
      def __init__(self, path, content):
        self.path = path
        self.content = content

    files_content = [
      FileObj("file1.py", "content1"),
      FileObj("dir/file2.py", "content2")
    ]

    modified = FileReplacer.replace_files(self.repo_path, files_content)

    assert "file1.py" in modified
    assert "dir/file2.py" in modified


if __name__ == "__main__":
  unittest.main()
