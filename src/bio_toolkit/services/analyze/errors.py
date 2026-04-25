from bio_toolkit.shared.errors import ServiceError


class AnalyzeServiceError(ServiceError):
    """Raised when the analyze service cannot complete the requested analysis."""


__all__ = ["AnalyzeServiceError"]
