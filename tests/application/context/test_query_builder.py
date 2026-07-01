import unittest

from src.application.context.query_builder import build_rag_query


class TestBuildRagQuery(unittest.TestCase):

  def test_build_rag_query_truncates_per_file(self):
    long_content = "x" * 1000
    result = build_rag_query([long_content], per_file=500)
    self.assertLessEqual(len(result), 500)

  def test_build_rag_query_truncates_global_limit(self):
    items = ["a" * 500] * 20
    result = build_rag_query(items, char_limit=8000, per_file=500)
    self.assertLessEqual(len(result), 8000)

  def test_build_rag_query_returns_empty_for_empty_input(self):
    result = build_rag_query([])
    self.assertEqual(result, "")

  def test_build_rag_query_returns_empty_for_blank_contents(self):
    result = build_rag_query(["   ", "\t\n", ""])
    self.assertEqual(result, "")

  def test_build_rag_query_joins_multiple_items(self):
    result = build_rag_query(["hello", "world"])
    self.assertIn("hello", result)
    self.assertIn("world", result)

  def test_build_rag_query_single_item(self):
    result = build_rag_query(["def foo(): pass"])
    self.assertEqual(result, "def foo(): pass")


if __name__ == "__main__":
  unittest.main()
