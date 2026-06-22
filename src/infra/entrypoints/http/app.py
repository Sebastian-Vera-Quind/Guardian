import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST

from .errors import (
    APIKeyMissingError, APIKeyInvalidError, WorkflowValidationError
)
from .endpoints import manual_chat_router


logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI(title="Guardian Server")

@app.exception_handler(APIKeyMissingError)
async def api_key_missing_handler(
  request: Request,
  exc: APIKeyMissingError
):
  return JSONResponse(
    status_code=HTTP_401_UNAUTHORIZED,
    content={"detail": "Unauthorized"}
  )

@app.exception_handler(APIKeyInvalidError)
async def api_key_invalid_handler(
  request: Request,
  exc: APIKeyInvalidError
):
  return JSONResponse(
    status_code=HTTP_403_FORBIDDEN,
    content={"detail": "Forbidden"}
  )

@app.exception_handler(WorkflowValidationError)
async def workflow_validation_error_handler(
  request: Request,
  exc: WorkflowValidationError
):
  return JSONResponse(
    status_code=HTTP_400_BAD_REQUEST,
    content={"detail": str(exc)}
  )

app.include_router(manual_chat_router)

