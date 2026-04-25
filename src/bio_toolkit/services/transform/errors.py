from bio_toolkit.shared.errors import ServiceError


class TransformServiceError(ServiceError):
    """Raised when the transform service cannot complete the requested transform."""


__all__ = ["TransformServiceError"]
