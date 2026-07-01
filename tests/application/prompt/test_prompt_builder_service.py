import unittest
from unittest.mock import MagicMock

from src.application.prompt import PromptBuilderService
from src.domain.models import PromptScope, UnknownPromptScopeError


class TestPromptBuilderService(unittest.TestCase):

  def setUp(self):
    self.renderer = MagicMock()
    self.service = PromptBuilderService(self.renderer)

  def test_build_for_scope_returns_rendered_prompt(self):
    self.renderer.render_scope.return_value = "RENDERED"
    result = self.service.build_for_scope(
      PromptScope.CHECKLIST, {"code": "x = 1"}
    )
    self.assertEqual(result, "RENDERED")
    self.renderer.render_scope.assert_called_once()

  def test_build_for_scope_invalid_scope_raises(self):
    with self.assertRaises(UnknownPromptScopeError):
      self.service.build_for_scope("checklist", {})

  def test_sanitize_removes_control_characters(self):
    dirty = "hello\x00wor\x07ld"
    self.assertEqual(self.service.sanitize(dirty), "helloworld")

  def test_sanitize_removes_blank_lines(self):
    dirty = "line1\n\n   \nline2"
    self.assertEqual(self.service.sanitize(dirty), "line1\nline2")

  def test_sanitize_attributes_sanitizes_only_strings(self):
    self.renderer.render_scope.return_value = "ok"
    attributes = {"code": "a\x00\n\nb", "count": 3, "flag": True}
    self.service.build_for_scope(PromptScope.CHECKLIST, attributes)
    passed = self.renderer.render_scope.call_args[0][1]
    self.assertEqual(passed["code"], "a\nb")
    self.assertEqual(passed["count"], 3)
    self.assertEqual(passed["flag"], True)

  def test_build_from_template_delegates_with_sanitized_attrs(self):
    self.renderer.render_template.return_value = "OUT"
    result = self.service.build_from_template(
      "{{ code }}", {"code": "x\x00\n\ny"}
    )
    self.assertEqual(result, "OUT")
    template_arg, attrs_arg = self.renderer.render_template.call_args[0]
    self.assertEqual(template_arg, "{{ code }}")
    self.assertEqual(attrs_arg["code"], "x\ny")


if __name__ == "__main__":
  unittest.main()
