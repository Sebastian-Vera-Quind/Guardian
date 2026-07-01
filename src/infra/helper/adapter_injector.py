from enum import Enum
from typing import Callable, Dict, Union

from src.domain.ports.output import (
  MetadataReader,
  RepositoryCloner,
  RulesRepository,
  ProjectFieldsRepository,
  CodingStandardsSearch,
  VectorSearchRepository,
  TlmClient,
  AIProvider,
)

class OutPortType(str, Enum):
  MetadataReader = "metadata_reader"
  RepositoryCloner = "repository_cloner"
  RulesRepository = "rules_repository"
  AIProvider = "ai_provider"
  TlmClient = "tlm_client"
  VectorSearchRepository = "vector_search_repository"
  CodingStandardsSearch = "coding_standards_search"
  ProjectFieldsRepository = "project_fields_repository"

_OutPort = Union[
  MetadataReader,
  RepositoryCloner,
  RulesRepository,
  AIProvider,
  TlmClient,
  VectorSearchRepository,
  CodingStandardsSearch,
  ProjectFieldsRepository,
]


def _create_metadata_reader() -> MetadataReader:
  from src.infra.adapters.github import GithubMetadataReader
  return GithubMetadataReader()

def _create_repository_cloner() -> RepositoryCloner:
  from src.infra.adapters.git import GitRepositoryCloner
  return GitRepositoryCloner()


def _create_rules_repository() -> RulesRepository:
  from src.infra.adapters.db import PostgresRulesRepositoryAdapter
  return PostgresRulesRepositoryAdapter()


def _create_ai_provider() -> AIProvider:
  from src.infra.adapters.ai.litellm_provider import LiteLLMProvider
  return LiteLLMProvider()


def _create_tlm_client() -> TlmClient:
  from src.infra.adapters.tlm.tlm_http_client import TlmHttpClient
  return TlmHttpClient()


def _create_vector_search_repository() -> VectorSearchRepository:
  from src.infra.adapters.db.pgvector_arch_doc_repository import (
    PgVectorArchDocRepository,
  )
  from src.infra.helper.inject import inject
  ai_provider = inject(OutPortType.AIProvider)
  tlm_client = inject(OutPortType.TlmClient)
  return PgVectorArchDocRepository(
    ai_provider=ai_provider, tlm_client=tlm_client
  )


def _create_coding_standards_search() -> CodingStandardsSearch:
  from src.infra.adapters.tlm.coding_standards_search import (
    HttpCodingStandardsSearch,
  )
  from src.infra.helper.inject import inject
  tlm_client = inject(OutPortType.TlmClient)
  return HttpCodingStandardsSearch(tlm_client=tlm_client)


def _create_project_fields_repository() -> ProjectFieldsRepository:
  from src.infra.adapters.db.project_fields_repository import (
    ProjectFieldsRepositoryAdapter,
  )
  from src.infra.helper.inject import inject
  tlm_client = inject(OutPortType.TlmClient)
  return ProjectFieldsRepositoryAdapter(tlm_client=tlm_client)


_out_port_factories: Dict[OutPortType, Callable[[], _OutPort]] = {
  OutPortType.MetadataReader: _create_metadata_reader,
  OutPortType.RepositoryCloner: _create_repository_cloner,
  OutPortType.RulesRepository: _create_rules_repository,
  OutPortType.AIProvider: _create_ai_provider,
  OutPortType.TlmClient: _create_tlm_client,
  OutPortType.VectorSearchRepository: _create_vector_search_repository,
  OutPortType.CodingStandardsSearch: _create_coding_standards_search,
  OutPortType.ProjectFieldsRepository: _create_project_fields_repository,
}


class OutPortInjector:
  _instances: Dict[OutPortType, _OutPort] = {}

  def __init__(self) -> None:
    raise TypeError("OutPortInjector cannot be instantiated")

  @classmethod
  def get_out_port(cls, port_type: OutPortType) -> _OutPort:
    if port_type not in cls._instances:
      cls._instances[port_type] = _out_port_factories[port_type]()
    return cls._instances[port_type]
