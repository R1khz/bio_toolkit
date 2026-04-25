from bio_toolkit.shared.errors import ServiceError


class FetchServiceError(ServiceError):
    """Raised when the fetch service cannot complete a fetch request."""


__all__ = ["FetchServiceError"]
