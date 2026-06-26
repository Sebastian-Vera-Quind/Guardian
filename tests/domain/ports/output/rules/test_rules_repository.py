import unittest
from abc import ABC

from src.domain.ports.output.repository.rules_repository import (
  RulesRepository,
)


class TestRulesRepository(unittest.TestCase):
  """Validar que protocolo RulesRepository está correctamente definido."""

  def test_rules_repository_is_abc(self) -> None:
    """Validar que RulesRepository es una clase abstracta."""
    self.assertTrue(issubclass(RulesRepository, ABC))

  def test_rules_repository_has_get_project_context_method(self) -> None:
    """Validar que RulesRepository tiene método get_project_context."""
    self.assertTrue(
      hasattr(RulesRepository, "get_project_context")
    )

  def test_get_project_context_is_abstract(self) -> None:
    """Validar que get_project_context es abstracto."""
    # No se puede instanciar RulesRepository directamente
    with self.assertRaises(TypeError):
      RulesRepository()  # type: ignore
