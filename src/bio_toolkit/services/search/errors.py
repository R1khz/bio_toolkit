from bio_toolkit.shared.errors import ServiceError


class SearchServiceError(ServiceError):
    """Raised when the search service cannot complete a search request."""


__all__ = ["SearchServiceError"]
