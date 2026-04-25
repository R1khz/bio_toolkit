from bio_toolkit.shared.errors import ServiceError


class AnnotateServiceError(ServiceError):
    """Raised when the annotate service cannot complete the requested annotation."""


__all__ = ["AnnotateServiceError"]
