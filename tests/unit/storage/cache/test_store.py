from bio_toolkit.storage.cache.store import CacheStore


def test_cache_store_class_is_available() -> None:
    assert CacheStore is not None
