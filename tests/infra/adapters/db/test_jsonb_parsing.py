import unittest

from src.infra.adapters.db.postgres_rules_repository import (
  _parse_json_field,
)


class TestParseJsonField(unittest.TestCase):
  """Tests exhaustivos para _parse_json_field()."""

  def test_parse_valid_json_string_to_list(self) -> None:
    """Validar parseo de string JSON a lista."""
    result = _parse_json_field('["item1", "item2"]')
    self.assertEqual(result, ["item1", "item2"])

  def test_parse_valid_json_string_to_dict(self) -> None:
    """Validar parseo de string JSON a dict."""
    result = _parse_json_field('{"key": "value"}')
    self.assertEqual(result, {"key": "value"})

  def test_parse_dict_returns_dict(self) -> None:
    """Validar que dict se retorna como es."""
    data = {"key": "value"}
    result = _parse_json_field(data)
    self.assertEqual(result, data)

  def test_parse_list_returns_list(self) -> None:
    """Validar que list se retorna como es."""
    data = ["item1", "item2"]
    result = _parse_json_field(data)
    self.assertEqual(result, data)

  def test_parse_none_returns_empty_list(self) -> None:
    """Validar que None retorna []."""
    result = _parse_json_field(None)
    self.assertEqual(result, [])

  def test_parse_invalid_json_string_returns_empty_list(self) -> None:
    """Validar que JSON inválido retorna []."""
    result = _parse_json_field("invalid json {")
    self.assertEqual(result, [])

  def test_parse_empty_string_returns_empty_list(self) -> None:
    """Validar que string vacío retorna []."""
    result = _parse_json_field("")
    self.assertEqual(result, [])

  def test_parse_json_null_returns_empty_list(self) -> None:
    """Validar que "null" JSON retorna []."""
    result = _parse_json_field("null")
    self.assertEqual(result, [])

  def test_parse_json_empty_list(self) -> None:
    """Validar parseo de lista JSON vacía."""
    result = _parse_json_field("[]")
    self.assertEqual(result, [])

  def test_parse_json_empty_object(self) -> None:
    """Validar parseo de objeto JSON vacío."""
    result = _parse_json_field("{}")
    self.assertEqual(result, {})

  def test_parse_json_with_nested_structure(self) -> None:
    """Validar parseo de JSON anidado."""
    json_str = '{"outer": {"inner": ["value"]}}'
    result = _parse_json_field(json_str)
    self.assertEqual(result, {"outer": {"inner": ["value"]}})

  def test_parse_json_with_numbers(self) -> None:
    """Validar parseo de JSON con números."""
    result = _parse_json_field('[1, 2, 3]')
    self.assertEqual(result, [1, 2, 3])

  def test_parse_json_with_booleans(self) -> None:
    """Validar parseo de JSON con booleanos."""
    result = _parse_json_field('{"active": true, "deleted": false}')
    self.assertEqual(result, {"active": True, "deleted": False})
