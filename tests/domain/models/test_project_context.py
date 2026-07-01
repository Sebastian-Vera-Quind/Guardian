import unittest

from src.domain.models.project_context import ProjectContext


class TestProjectContext(unittest.TestCase):
  """Validar creación e inmutabilidad de ProjectContext."""

  def test_create_project_context(self) -> None:
    """Validar que se puede crear ProjectContext."""
    context = ProjectContext(
      project_code="test-project",
      scope="structure",
      data={"key": "value"},
    )
    self.assertEqual(context.project_code, "test-project")
    self.assertEqual(context.scope, "structure")
    self.assertEqual(context.data, {"key": "value"})

  def test_project_context_is_frozen(self) -> None:
    """Validar que ProjectContext es inmutable."""
    context = ProjectContext(
      project_code="test-project",
      scope="structure",
      data={"key": "value"},
    )
    with self.assertRaises(Exception):
      context.project_code = "new-code"  # type: ignore

  def test_project_context_with_empty_data(self) -> None:
    """Validar ProjectContext con data vacía."""
    context = ProjectContext(
      project_code="test-project",
      scope="structure",
      data={},
    )
    self.assertEqual(context.data, {})

  def test_project_context_with_nested_data(self) -> None:
    """Validar ProjectContext con data anidada."""
    data = {
      "stack": ["python", "fastapi"],
      "structure": {"src": "directory"},
    }
    context = ProjectContext(
      project_code="test-project",
      scope="master",
      data=data,
    )
    self.assertEqual(context.data, data)
