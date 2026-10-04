from typing import Any, List, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[List[Any]] = None,
        retryable: bool = False
    ):
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or []
        self.retryable = retryable


class AuthenticationError(AppException):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTHENTICATION_FAILED",
            message=message,
            retryable=False
        )


class ResourceNotFoundError(AppException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=f"{resource} with id '{resource_id}' was not found",
            retryable=False
        )


class StateConflictError(AppException):
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="STATE_CONFLICT",
            message=message,
            retryable=False
        )


class ValidationError(AppException):
    def __init__(self, message: str, details: Optional[List[Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
            retryable=False
        )


class RateLimitExceededError(AppException):
    def __init__(self, message: str = "Rate limit exceeded. Please wait."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            retryable=True
        )


class AIProviderError(AppException):
    def __init__(self, message: str, retryable: bool = True):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="AI_PROVIDER_ERROR",
            message=message,
            retryable=retryable
        )
