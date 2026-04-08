# app/middleware/request_id.py
import uuid

import structlog
from fastapi import FastAPI, Request
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from ..core.config import settings


class LoggerMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to the context variables.

    Parameters
    ----------
    app: FastAPI
        The FastAPI application instance.
    """

    def __init__(self, app: FastAPI) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Add request ID to the context variables and log request/response.
        """
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            client_host=request.client.host if request.client else None,
            path=request.url.path,
            method=request.method,
        )

        log_data = {}

        # Capture Request Body
        if settings.LOG_REQUEST_BODY:
            try:
                body = await request.body()
                # Store body back into request object so it can be read again by the handler
                # Note: request.body() caches the result in request._body
                if body:
                    body_str = body.decode("utf-8", errors="replace")
                    if len(body_str) > settings.LOG_MAX_BODY_SIZE:
                        body_str = body_str[:settings.LOG_MAX_BODY_SIZE] + "... [truncated]"
                    log_data["request_body"] = body_str
            except Exception as e:
                log_data["request_body_error"] = str(e)

        # Process Request
        response = await call_next(request)

        # Capture Response Body
        if settings.LOG_RESPONSE_BODY:
            try:
                # To read the response body, we must iterate over it
                # This can be tricky for StreamingResponses
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                # Re-create the body iterator so it can be sent to the client
                response.body_iterator = iterate_in_threadpool(iter([response_body]))

                if response_body:
                    response_str = response_body.decode("utf-8", errors="replace")
                    if len(response_str) > settings.LOG_MAX_BODY_SIZE:
                        response_str = response_str[:settings.LOG_MAX_BODY_SIZE] + "... [truncated]"
                    log_data["response_body"] = response_str
            except Exception as e:
                log_data["response_body_error"] = str(e)

        structlog.contextvars.bind_contextvars(
            status_code=response.status_code,
            **log_data
        )
        
        # Finally log everything if it's not a health check or similar noise
        if not request.url.path.endswith(("/health", "/docs", "/openapi.json")):
            structlog.get_logger("request_logger").info("Request processed")

        response.headers["X-Request-ID"] = request_id
        return response
