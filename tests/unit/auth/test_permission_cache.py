"""Tests unitarios para PermissionCache — in-memory TTL cache."""

import time

from app.modules.auth.infrastructure.cache.permission_cache import PermissionCache


class TestPermissionCache:
    def test_set_and_get(self):
        cache = PermissionCache(ttl_seconds=60)
        cache.set("user1", {"a", "b"})
        assert cache.get("user1") == {"a", "b"}

    def test_get_nonexistent_returns_none(self):
        cache = PermissionCache(ttl_seconds=60)
        assert cache.get("nobody") is None

    def test_invalidate(self):
        cache = PermissionCache(ttl_seconds=60)
        cache.set("user1", {"a"})
        cache.invalidate("user1")
        assert cache.get("user1") is None

    def test_clear(self):
        cache = PermissionCache(ttl_seconds=60)
        cache.set("u1", {"a"})
        cache.set("u2", {"b"})
        cache.clear()
        assert cache.get("u1") is None
        assert cache.get("u2") is None

    def test_ttl_expiration(self):
        cache = PermissionCache(ttl_seconds=0)  # Expires immediately
        cache.set("user1", {"a"})
        time.sleep(0.01)
        assert cache.get("user1") is None

    def test_invalidate_nonexistent_no_error(self):
        cache = PermissionCache(ttl_seconds=60)
        cache.invalidate("nobody")  # Should not raise
