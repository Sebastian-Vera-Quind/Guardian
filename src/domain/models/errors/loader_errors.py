from src.domain.models import AgenticError


class LoaderNodeError(AgenticError):
    pass


class SanitizationError(LoaderNodeError):
    pass


class MetadataExtractionError(LoaderNodeError):
    pass


class InvalidJSONLError(LoaderNodeError):
    pass
