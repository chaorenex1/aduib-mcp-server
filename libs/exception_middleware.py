"""Global exception handling middleware for crash prevention."""
import asyncio
import logging
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class GlobalExceptionMiddleware(BaseHTTPMiddleware):
    """Catch all unhandled exceptions to prevent service crashes."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except asyncio.CancelledError:
            # Allow cancellation to propagate (graceful shutdown)
            raise
        except MemoryError as e:
            logger.critical(f"Memory error: {e}")
            return JSONResponse(
                {"error": "Service temporarily unavailable due to resource constraints"},
                status_code=503
            )
        except Exception as e:
            # Log full traceback
            logger.exception(f"Unhandled exception in request {request.url.path}")

            # Return generic error (don't leak internal info)
            trace_id = getattr(request.state, 'trace_id', None)
            return JSONResponse(
                {
                    "error": "Internal server error",
                    "type": type(e).__name__,
                    "request_id": trace_id
                },
                status_code=500
            )


class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Circuit breaker: temporarily reject requests after consecutive failures."""

    def __init__(
        self,
        app,
        failure_threshold: int = 10,
        reset_timeout: float = 60.0,
        half_open_requests: int = 3
    ):
        super().__init__(app)
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_requests = half_open_requests
        
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.circuit_open = False
        self.half_open_successes = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        now = time.time()

        # Check circuit state
        if self.circuit_open:
            if now - self.last_failure_time > self.reset_timeout:
                # Try half-open state
                logger.info("Circuit breaker: entering half-open state")
                self.circuit_open = False
                self.half_open_successes = 0
            else:
                logger.warning(f"Circuit breaker OPEN: rejecting request to {request.url.path}")
                return JSONResponse(
                    {"error": "Service temporarily unavailable (circuit open)"},
                    status_code=503
                )

        try:
            response = await call_next(request)
            
            if response.status_code < 500:
                # Success - reset failure count
                if not self.circuit_open:
                    self.failure_count = 0
                else:
                    self.half_open_successes += 1
                    if self.half_open_successes >= self.half_open_requests:
                        logger.info("Circuit breaker: closing circuit after successful requests")
                        self.circuit_open = False
                        self.failure_count = 0
            else:
                # Server error
                self._record_failure(now)
                
            return response
            
        except Exception as e:
            self._record_failure(now)
            raise

    def _record_failure(self, now: float):
        """Record a failure and potentially open the circuit."""
        self.failure_count += 1
        self.last_failure_time = now

        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            logger.warning(
                f"Circuit breaker OPENED after {self.failure_count} consecutive failures"
            )
