from abc import ABC, abstractmethod
from src.domain.models.state.repository import RepositoryMetadata


class MetadataReader(ABC):
    @abstractmethod
    def extract_from_repository(self, repo_data: dict) -> RepositoryMetadata:
        ...
