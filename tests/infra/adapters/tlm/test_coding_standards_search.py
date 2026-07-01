import unittest
from unittest.mock import MagicMock

from src.domain.models.retrieved_context import SimilarStandard
from src.infra.adapters.tlm.coding_standards_search import (
  HttpCodingStandardsSearch,
)


class TestHttpCodingStandardsSearch(unittest.TestCase):

  def test_find_returns_standards_above_floor(self):
    tlm = MagicMock()
    tlm.search_coding_standards.return_value = [
      SimilarStandard(name="PEP8", description="style guide"),
      SimilarStandard(name="Typing", description="type hints"),
    ]
    search = HttpCodingStandardsSearch(tlm_client=tlm)
    result = search.find_similar_coding_standards("PROJ", "query")

    self.assertEqual(len(result), 2)
    names = [r.name for r in result]
    self.assertIn("PEP8", names)
    self.assertIn("Typing", names)

  def test_find_filters_below_floor(self):
    # The floor filtering is applied in the TlmClient layer;
    # HttpCodingStandardsSearch returns whatever TlmClient returns.
    tlm = MagicMock()
    tlm.search_coding_standards.return_value = []
    search = HttpCodingStandardsSearch(tlm_client=tlm)
    result = search.find_similar_coding_standards("PROJ", "query")

    self.assertEqual(result, [])

  def test_find_returns_empty_on_exception(self):
    tlm = MagicMock()
    tlm.search_coding_standards.side_effect = RuntimeError("boom")
    search = HttpCodingStandardsSearch(tlm_client=tlm)
    result = search.find_similar_coding_standards("PROJ", "query")

    self.assertEqual(result, [])


if __name__ == "__main__":
  unittest.main()
