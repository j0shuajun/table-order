"""Domain-level errors carrying the HTTP status the API layer should surface.

Services raise these instead of FastAPI ``HTTPException`` so they stay framework
independent; a single exception handler maps them to ``{"detail": ...}`` responses.
"""


class DomainError(Exception):
    status_code: int = 400

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class ValidationError(DomainError):
    status_code = 400


class AuthError(DomainError):
    status_code = 401


class ForbiddenError(DomainError):
    status_code = 403


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409
