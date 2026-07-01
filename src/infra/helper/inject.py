from __future__ import annotations
from typing import Literal, Union, overload

from src.domain.ports.input import (
  WorkflowExecutor,
  ContextRetriever,
  CloneService,
)
from src.domain.ports.output import (
  MetadataReader,
  RepositoryCloner,
  RulesRepository,
  AIProvider,
  TlmClient,
  VectorSearchRepository,
  CodingStandardsSearch,
  ProjectFieldsRepository,
)
from .adapter_injector import OutPortType, OutPortInjector
from .usecase_injector import InPortType, UseCaseInjector


@overload
def inject(
  dependency_type: Literal[InPortType.WorkFlowExcecutor],
) -> WorkflowExecutor: ...

@overload
def inject(
  dependency_type: Literal[InPortType.CloneService],
) -> CloneService: ...

@overload
def inject(
  dependency_type: Literal[InPortType.ContextRetrievalService],
) -> ContextRetriever: ...

@overload
def inject(
  dependency_type: Literal[OutPortType.MetadataReader],
) -> MetadataReader: ...

@overload
def inject(
  dependency_type: Literal[OutPortType.RepositoryCloner],
) -> RepositoryCloner: ...

@overload
def inject(
  dependency_type: Literal[OutPortType.RulesRepository],
) -> RulesRepository: ...

@overload
def inject(
  dependency_type: Literal[OutPortType.AIProvider],
) -> AIProvider: ...

@overload
def inject(
  dependency_type: Literal[OutPortType.TlmClient],
) -> TlmClient: ...


@overload
def inject(
  dependency_type: Literal[OutPortType.VectorSearchRepository],
) -> VectorSearchRepository: ...


@overload
def inject(
  dependency_type: Literal[OutPortType.CodingStandardsSearch],
) -> CodingStandardsSearch: ...

@overload
def inject(
  dependency_type: Literal[OutPortType.ProjectFieldsRepository],
) -> ProjectFieldsRepository: ...

def inject(
  dependency_type: Union[InPortType, OutPortType],
) -> Union[
  WorkflowExecutor,
  CloneService,
  ContextRetriever,
  MetadataReader,
  RepositoryCloner,
  RulesRepository,
  AIProvider,
  TlmClient,
  VectorSearchRepository,
  CodingStandardsSearch,
  ProjectFieldsRepository,
]:
  if dependency_type in OutPortType.__members__.values():
    return OutPortInjector.get_out_port(  # type: ignore[arg-type]
      dependency_type  # type: ignore[arg-type]
    )
  return UseCaseInjector.get_use_case(  # type: ignore[arg-type]
    dependency_type  # type: ignore[arg-type]
  )
