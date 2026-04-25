from bio_toolkit.shared.errors import ServiceError


class CompareServiceError(ServiceError):
    """Raised when the compare service cannot complete the requested comparison."""


__all__ = ["CompareServiceError"]
