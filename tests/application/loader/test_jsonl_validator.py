import unittest
import logging
from unittest.mock import patch
from src.application.loader.jsonl_validator import JSONLValidator
from src.domain.models.state.file import FileContent


class TestJSONLValidatorIsValidJsonl(unittest.TestCase):

    def test_is_valid_jsonl_empty_string_returns_false(self):
        self.assertFalse(JSONLValidator.is_valid_jsonl(""))

    def test_is_valid_jsonl_whitespace_only_returns_false(self):
        self.assertFalse(JSONLValidator.is_valid_jsonl("   \n\t\n"))

    def test_is_valid_jsonl_valid_multiline_returns_true(self):
        content = '{"a": 1}\n{"b": 2}\n{"c": 3}'
        self.assertTrue(JSONLValidator.is_valid_jsonl(content))

    def test_is_valid_jsonl_single_valid_line_returns_true(self):
        content = '{"key": "value"}'
        self.assertTrue(JSONLValidator.is_valid_jsonl(content))

    def test_is_valid_jsonl_invalid_json_returns_false(self):
        content = '{"a": 1}\nnot-json\n{"b": 2}'
        self.assertFalse(JSONLValidator.is_valid_jsonl(content))

    def test_is_valid_jsonl_partial_invalid_json_returns_false(self):
        content = '{"a": 1}\n{broken'
        self.assertFalse(JSONLValidator.is_valid_jsonl(content))

    def test_is_valid_jsonl_ignores_empty_lines_between_valid_json(self):
        content = '{"a": 1}\n\n{"b": 2}'
        self.assertTrue(JSONLValidator.is_valid_jsonl(content))


class TestJSONLValidatorExtractAttributionFile(unittest.TestCase):

    def _make_file(self, path: str, content: str, extension: str = "jsonl") -> FileContent:
        return {"path": path, "content": content, "extension": extension}

    def test_extract_attribution_found_and_valid_extracts_content(self):
        valid_jsonl = '{"agent": "gpt-4"}\n{"agent": "claude"}'
        files = [
            self._make_file(".devcore-attribution.jsonl", valid_jsonl),
            self._make_file("src/main.py", "print('hello')", "py"),
        ]
        remaining, attribution = JSONLValidator.extract_attribution_file(files)
        self.assertEqual(attribution, valid_jsonl)

    def test_extract_attribution_removes_file_from_list(self):
        valid_jsonl = '{"agent": "gpt-4"}'
        files = [
            self._make_file(".devcore-attribution.jsonl", valid_jsonl),
            self._make_file("src/main.py", "x = 1", "py"),
        ]
        remaining, _ = JSONLValidator.extract_attribution_file(files)
        paths = [f["path"] for f in remaining]
        self.assertNotIn(".devcore-attribution.jsonl", paths)
        self.assertIn("src/main.py", paths)

    def test_extract_attribution_found_invalid_logs_warning_returns_none(self):
        invalid_content = "not-json-at-all"
        files = [
            self._make_file(".devcore-attribution.jsonl", invalid_content),
        ]
        with self.assertLogs("src.application.loader.jsonl_validator", level=logging.WARNING) as log_ctx:
            _, attribution = JSONLValidator.extract_attribution_file(files)
        self.assertIsNone(attribution)
        self.assertTrue(any("Invalid JSONL" in msg for msg in log_ctx.output))

    def test_extract_attribution_not_found_returns_none(self):
        files = [
            self._make_file("src/main.py", "x = 1", "py"),
            self._make_file("README.md", "# title", "md"),
        ]
        remaining, attribution = JSONLValidator.extract_attribution_file(files)
        self.assertIsNone(attribution)
        self.assertEqual(len(remaining), 2)

    def test_extract_attribution_nested_path_is_detected(self):
        valid_jsonl = '{"agent": "claude"}'
        files = [
            self._make_file("some/folder/.devcore-attribution.jsonl", valid_jsonl),
            self._make_file("src/app.py", "pass", "py"),
        ]
        remaining, attribution = JSONLValidator.extract_attribution_file(files)
        self.assertEqual(attribution, valid_jsonl)
        paths = [f["path"] for f in remaining]
        self.assertNotIn("some/folder/.devcore-attribution.jsonl", paths)

    def test_extract_attribution_empty_files_list_returns_none(self):
        remaining, attribution = JSONLValidator.extract_attribution_file([])
        self.assertIsNone(attribution)
        self.assertEqual(remaining, [])


if __name__ == "__main__":
    unittest.main()
