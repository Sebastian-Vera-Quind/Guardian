import unittest
from unittest.mock import MagicMock, patch

from src.application.context.context_retrieval_service import (
  ContextRetrievalService,
)
from src.domain.models.errors import RulesRepositoryError
from src.domain.models.project_context import ProjectContext
from src.domain.models.project_fields import ProjectFields
from src.domain.models.retrieved_context import RetrievedContext, SimilarStandard


def _make_service(rules=None, vector=None, standards=None, fields=None):
  rules = rules or MagicMock()
  vector = vector or MagicMock()
  standards = standards or MagicMock()
  fields = fields or MagicMock()
  return ContextRetrievalService(
    rules=rules, vector=vector, standards=standards, fields=fields
  )


def _make_project_context(coding_standards=None):
  data = {"coding_standards": coding_standards or []}
  return ProjectContext(
    project_code="PROJ", scope="review", data=data
  )


class TestRetrieveUsesRulesAsCodingStandards(unittest.TestCase):

  def test_retrieve_uses_rules_coding_standards_as_base(self):
    rules = MagicMock()
    rules.get_project_context.return_value = _make_project_context(
      ["rule1", "rule2"]
    )
    vector = MagicMock()
    vector.search_similar_chunks.return_value = []
    standards = MagicMock()
    standards.find_similar_coding_standards.return_value = []
    fields = MagicMock()
    fields.get_project_fields.return_value = ProjectFields()

    svc = _make_service(rules=rules, vector=vector,
                        standards=standards, fields=fields)
    ctx = svc.retrieve("PROJ", "")

    self.assertIn("rule1", ctx.active_rules)
    self.assertIn("rule2", ctx.active_rules)

  def test_retrieve_fallback_on_rules_error(self):
    rules = MagicMock()
    rules.get_project_context.side_effect = RulesRepositoryError(
      "db down"
    )
    vector = MagicMock()
    vector.search_similar_chunks.return_value = []
    standards = MagicMock()
    standards.find_similar_coding_standards.return_value = []
    fields = MagicMock()
    fields.get_project_fields.return_value = ProjectFields()

    svc = _make_service(rules=rules, vector=vector,
                        standards=standards, fields=fields)
    ctx = svc.retrieve("PROJ", "")

    self.assertTrue(len(ctx.active_rules) >= 1)


class TestRetrieveVectorChunks(unittest.TestCase):

  def test_retrieve_appends_vector_chunks_when_query_not_empty(self):
    rules = MagicMock()
    rules.get_project_context.return_value = _make_project_context(
      ["base_rule"]
    )
    vector = MagicMock()
    vector.search_similar_chunks.return_value = ["arch_chunk"]
    standards = MagicMock()
    standards.find_similar_coding_standards.return_value = []
    fields = MagicMock()
    fields.get_project_fields.return_value = ProjectFields()

    svc = _make_service(rules=rules, vector=vector,
                        standards=standards, fields=fields)
    ctx = svc.retrieve("PROJ", "some query")

    wrapped = [r for r in ctx.active_rules if "arch_chunk" in r]
    self.assertTrue(len(wrapped) >= 1)

  def test_retrieve_skips_vector_when_query_empty(self):
    rules = MagicMock()
    rules.get_project_context.return_value = _make_project_context(
      ["base_rule"]
    )
    vector = MagicMock()
    fields = MagicMock()
    fields.get_project_fields.return_value = ProjectFields()
    standards = MagicMock()
    standards.find_similar_coding_standards.return_value = []

    svc = _make_service(rules=rules, vector=vector,
                        standards=standards, fields=fields)
    svc.retrieve("PROJ", "  ")

    vector.search_similar_chunks.assert_not_called()

  def test_retrieve_vector_fail_open(self):
    rules = MagicMock()
    rules.get_project_context.return_value = _make_project_context(
      ["rule1"]
    )
    vector = MagicMock()
    vector.search_similar_chunks.side_effect = RuntimeError("vector err")
    standards = MagicMock()
    standards.find_similar_coding_standards.return_value = []
    fields = MagicMock()
    fields.get_project_fields.return_value = ProjectFields()

    svc = _make_service(rules=rules, vector=vector,
                        standards=standards, fields=fields)
    ctx = svc.retrieve("PROJ", "query")

    self.assertIn("rule1", ctx.active_rules)


class TestRetrieveSimilarStandards(unittest.TestCase):

  def test_retrieve_appends_similar_standards_when_query_not_empty(self):
    rules = MagicMock()
    rules.get_project_context.return_value = _make_project_context([])
    vector = MagicMock()
    vector.search_similar_chunks.return_value = []
    standards = MagicMock()
    standards.find_similar_coding_standards.return_value = [
      SimilarStandard(name="PEP8", description="style guide")
    ]
    fields = MagicMock()
    fields.get_project_fields.return_value = ProjectFields()

    svc = _make_service(rules=rules, vector=vector,
                        standards=standards, fields=fields)
    ctx = svc.retrieve("PROJ", "some query")

    matches = [r for r in ctx.active_rules if "PEP8" in r]
    self.assertTrue(len(matches) >= 1)

  def test_retrieve_skips_standards_when_query_empty(self):
    rules = MagicMock()
    rules.get_project_context.return_value = _make_project_context([])
    vector = MagicMock()
    standards = MagicMock()
    fields = MagicMock()
    fields.get_project_fields.return_value = ProjectFields()

    svc = _make_service(rules=rules, vector=vector,
                        standards=standards, fields=fields)
    svc.retrieve("PROJ", "")

    standards.find_similar_coding_standards.assert_not_called()

  def test_retrieve_standards_fail_open(self):
    rules = MagicMock()
    rules.get_project_context.return_value = _make_project_context(
      ["rule1"]
    )
    vector = MagicMock()
    vector.search_similar_chunks.return_value = []
    standards = MagicMock()
    standards.find_similar_coding_standards.side_effect = RuntimeError(
      "standards err"
    )
    fields = MagicMock()
    fields.get_project_fields.return_value = ProjectFields()

    svc = _make_service(rules=rules, vector=vector,
                        standards=standards, fields=fields)
    ctx = svc.retrieve("PROJ", "query")

    self.assertIn("rule1", ctx.active_rules)


class TestRetrieveProjectFields(unittest.TestCase):

  def test_retrieve_fields_fail_open(self):
    rules = MagicMock()
    rules.get_project_context.return_value = _make_project_context([])
    vector = MagicMock()
    vector.search_similar_chunks.return_value = []
    standards = MagicMock()
    standards.find_similar_coding_standards.return_value = []
    fields = MagicMock()
    fields.get_project_fields.side_effect = RuntimeError("fields err")

    svc = _make_service(rules=rules, vector=vector,
                        standards=standards, fields=fields)
    ctx = svc.retrieve("PROJ", "query")

    self.assertIsNone(ctx.quality_gates)
    self.assertIsNone(ctx.constraints)
    self.assertIsNone(ctx.nfr_definition)
    self.assertIsNone(ctx.fitness_functions)

  def test_retrieve_returns_retrieved_context(self):
    rules = MagicMock()
    rules.get_project_context.return_value = _make_project_context(
      ["rule"]
    )
    vector = MagicMock()
    vector.search_similar_chunks.return_value = []
    standards = MagicMock()
    standards.find_similar_coding_standards.return_value = []
    fields = MagicMock()
    fields.get_project_fields.return_value = ProjectFields(
      quality_gates={"min": 80},
      constraints=None,
      nfr_definition=None,
      fitness_functions=["f1"],
    )

    svc = _make_service(rules=rules, vector=vector,
                        standards=standards, fields=fields)
    ctx = svc.retrieve("PROJ", "")

    self.assertIsInstance(ctx, RetrievedContext)
    self.assertEqual(ctx.quality_gates, {"min": 80})
    self.assertEqual(ctx.fitness_functions, ["f1"])


if __name__ == "__main__":
  unittest.main()
