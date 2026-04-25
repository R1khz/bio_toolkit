from bio_toolkit.shared.errors import ServiceError


class QueryServiceError(ServiceError):
    """Raised when the query service cannot complete a provider query."""


__all__ = ["QueryServiceError"]
