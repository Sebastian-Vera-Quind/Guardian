import os
import logging

from fastapi import Request
from starlette.responses import Response

from src.infra.entrypoints.http.errors import APIKeyInvalidError, APIKeyMissingError

logger = logging.getLogger(__name__)


async def validate_api_key(request: Request) -> Response:
  """Validate X-API-KEY header before processing the request."""
  api_key_header = request.headers.get("X-API-KEY")

  logger.info(f"API_KEY: {api_key_header}")
  if api_key_header is None:
    logger.warning("Request rejected: Missing X-API-KEY header")
    raise APIKeyMissingError()

  expected_key = os.getenv("GUARDIAN_API_KEY")
  
  logger.info(f"Expected API_KEY: {expected_key}")
  if api_key_header != expected_key:
    logger.warning(
      f"Request rejected: Invalid X-API-KEY"
    )
    raise APIKeyInvalidError()

