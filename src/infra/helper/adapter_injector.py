from enum import Enum
from typing import Any, Callable, Dict

class OutPortType(str, Enum):
  MetadataReader = "metadata_reader"
  RepositoryCloner = "repository_cloner"
  RulesRepository = "rules_repository"

def _create_metadata_reader() -> Any:
  from src.infra.adapters.github import GithubMetadataReader
  return GithubMetadataReader()

def _create_repository_cloner() -> Any:
  from src.infra.adapters.git import GitRepositoryCloner
  return GitRepositoryCloner()

def _create_rules_repository() -> Any:
  from src.infra.adapters.db import PostgresRulesRepositoryAdapter
  return PostgresRulesRepositoryAdapter()

_out_port_factories: Dict[OutPortType, Callable[[], Any]] = {
  OutPortType.MetadataReader: _create_metadata_reader,
  OutPortType.RepositoryCloner: _create_repository_cloner,
  OutPortType.RulesRepository: _create_rules_repository,
}


class OutPortInjector:
  _instances: Dict[OutPortType, Any] = {}

  def __init__(self) -> None:
    raise TypeError("OutPortInjector cannot be instantiated")

  @classmethod
  def get_out_port(cls, port_type: OutPortType) -> Any:
    if port_type not in cls._instances:
      cls._instances[port_type] = _out_port_factories[port_type]()
    return cls._instances[port_type]
