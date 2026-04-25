class BioToolkitError(RuntimeError):
    """Base error for application-level failures."""


class ProviderAdapterError(BioToolkitError):
    """Raised by external provider adapters."""


class StorageAdapterError(BioToolkitError):
    """Raised by cache or filesystem adapters."""


class ServiceError(BioToolkitError):
    """Raised when a service cannot complete a use case."""
