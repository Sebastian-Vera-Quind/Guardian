import unittest
from src.application.loader.sanitizer import CodeSanitizer
from src.domain.models import FileContent


class TestCodeSanitizerRemoveBlankLines(unittest.TestCase):

    def test_remove_blank_lines_eliminates_whitespace_only_lines(self):
        content = "def foo():\n   \n    pass\n\t\n    return 1"
        result = CodeSanitizer.remove_blank_lines(content)
        lines = result.split('\n')
        for line in lines:
            self.assertTrue(line.strip(), f"Expected no blank-only lines, found: {repr(line)}")

    def test_remove_blank_lines_preserves_code_lines(self):
        content = "line1\nline2\nline3"
        result = CodeSanitizer.remove_blank_lines(content)
        self.assertEqual(result, "line1\nline2\nline3")

    def test_remove_blank_lines_empty_string_returns_empty(self):
        result = CodeSanitizer.remove_blank_lines("")
        self.assertEqual(result, "")

    def test_remove_blank_lines_all_blank_returns_empty(self):
        content = "\n   \n\t\n"
        result = CodeSanitizer.remove_blank_lines(content)
        self.assertEqual(result.strip(), "")


class TestCodeSanitizerSanitizeFiles(unittest.TestCase):

    def test_sanitize_files_keeps_files_with_content(self):
        files: list[FileContent] = [
            {"path": "a.py", "content": "x = 1\ny = 2", "extension": "py"},
        ]
        result = CodeSanitizer.sanitize_files(files)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["path"], "a.py")

    def test_sanitize_files_removes_empty_files(self):
        files: list[FileContent] = [
            {"path": "empty.py", "content": "\n   \n\t\n", "extension": "py"},
            {"path": "code.py", "content": "print('hello')", "extension": "py"},
        ]
        result = CodeSanitizer.sanitize_files(files)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["path"], "code.py")

    def test_sanitize_files_strips_blank_lines_from_kept_files(self):
        files: list[FileContent] = [
            {"path": "a.py", "content": "x = 1\n\ny = 2\n   \nz = 3", "extension": "py"},
        ]
        result = CodeSanitizer.sanitize_files(files)
        self.assertEqual(len(result), 1)
        for line in result[0]["content"].split('\n'):
            self.assertTrue(line.strip())

    def test_sanitize_files_empty_list_returns_empty(self):
        result = CodeSanitizer.sanitize_files([])
        self.assertEqual(result, [])

    def test_sanitize_files_preserves_path_and_extension(self):
        files: list[FileContent] = [
            {"path": "src/mod.ts", "content": "const x = 1;", "extension": "ts"},
        ]
        result = CodeSanitizer.sanitize_files(files)
        self.assertEqual(result[0]["path"], "src/mod.ts")
        self.assertEqual(result[0]["extension"], "ts")


class TestCodeSanitizerCountLines(unittest.TestCase):

    def test_count_lines_single_file(self):
        files: list[FileContent] = [
            {"path": "a.py", "content": "line1\nline2\nline3", "extension": "py"},
        ]
        result = CodeSanitizer.count_lines(files)
        self.assertEqual(result, 3)

    def test_count_lines_multiple_files_sums_all(self):
        files: list[FileContent] = [
            {"path": "a.py", "content": "line1\nline2", "extension": "py"},
            {"path": "b.py", "content": "x\ny\nz", "extension": "py"},
        ]
        result = CodeSanitizer.count_lines(files)
        self.assertEqual(result, 5)

    def test_count_lines_empty_list_returns_zero(self):
        result = CodeSanitizer.count_lines([])
        self.assertEqual(result, 0)

    def test_count_lines_single_line_file(self):
        files: list[FileContent] = [
            {"path": "a.py", "content": "only one line", "extension": "py"},
        ]
        result = CodeSanitizer.count_lines(files)
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
