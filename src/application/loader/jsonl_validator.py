import json
import logging
from typing import List, Optional, Tuple
from src.domain.models import FileContent

logger = logging.getLogger(__name__)

ATTRIBUTION_FILENAME = ".devcore-attribution.jsonl"


class JSONLValidator:

    @staticmethod
    def is_valid_jsonl(content: str) -> bool:
        if not content.strip():
            return False
        for line in content.strip().split('\n'):
            if line.strip():
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    return False
        return True

    @staticmethod
    def extract_attribution_file(
        files: List[FileContent],
    ) -> Tuple[List[FileContent], Optional[str]]:
        remaining: List[FileContent] = []
        attribution_content: Optional[str] = None

        for file in files:
            if file["path"].endswith(ATTRIBUTION_FILENAME) or file["path"] == ATTRIBUTION_FILENAME:
                if JSONLValidator.is_valid_jsonl(file["content"]):
                    attribution_content = file["content"]
                else:
                    logger.warning("Invalid JSONL in %s, skipping", file["path"])
            else:
                remaining.append(file)

        return remaining, attribution_content
