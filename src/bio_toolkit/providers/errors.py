from bio_toolkit.shared.errors import ProviderAdapterError


class ProviderSelectionError(ProviderAdapterError):
    """Raised when provider adapter selection cannot be resolved."""


__all__ = ["ProviderSelectionError"]
