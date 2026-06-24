import os
import tempfile
import unittest

from src.application.clone.tree_builder import TreeBuilder
from src.application.clone.file_excluder import FileExcluder


class TestTreeBuilder(unittest.TestCase):
  """Tests para TreeBuilder."""

  def setUp(self):
    """Configura directorios temporales con archivos de prueba."""
    self.test_dir = tempfile.TemporaryDirectory()
    self.repo_path = self.test_dir.name

    os.makedirs(os.path.join(self.repo_path, "subdir"))
    with open(os.path.join(self.repo_path, "file1.py"), "w") as f:
      f.write("# code")
    with open(os.path.join(self.repo_path, "subdir", "file2.py"), "w") as f:
      f.write("# code")

    self.excluder = FileExcluder(self.repo_path)
    self.addCleanup(self.test_dir.cleanup)

  def test_build_tree_creates_valid_structure(self):
    """Test: build_tree crea estructura jerárquica válida."""
    tree = TreeBuilder.build_tree(self.repo_path, self.excluder)

    self.assertIn("name", tree)
    self.assertIn("type", tree)
    self.assertEqual(tree["type"], "directory")

  def test_build_tree_excludes_filtered_files(self):
    """Test: build_tree respeta FileExcluder."""
    image_path = os.path.join(self.repo_path, "image.png")
    with open(image_path, "wb") as f:
      f.write(b"fake image data")

    tree = TreeBuilder.build_tree(self.repo_path, self.excluder)

    def has_png(node):
      if node.get("name") == "image.png":
        return True
      for child in node.get("children", []):
        if has_png(child):
          return True
      return False

    self.assertFalse(has_png(tree))

  def test_build_tree_marks_new_files_correctly(self):
    """Test: archivos nuevos se marcan con is_new=True."""
    new_file_path = os.path.join(self.repo_path, "new_file.py")
    with open(new_file_path, "w") as f:
      f.write("# new")

    tree = TreeBuilder.build_tree(
      self.repo_path,
      self.excluder,
      added_files_set={new_file_path}
    )

    def find_file(node, name):
      if node.get("name") == name:
        return node
      for child in node.get("children", []):
        result = find_file(child, name)
        if result:
          return result
      return None

    new_file_node = find_file(tree, "new_file.py")
    if new_file_node:
      self.assertTrue(new_file_node.get("is_new", False))


if __name__ == "__main__":
  unittest.main()
