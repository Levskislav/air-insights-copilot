"""
tests/test_cache.py
===================
Unit tests for agent/cache.py - TTL cache with thread safety.
"""

import pytest
import threading
import time
from unittest.mock import patch

from agent.cache import (
    cache_key,
    cache_get,
    cache_set,
    cache_clear,
    cache_stats,
)


class TestCacheKey:
    """Tests for cache_key function."""
    
    def test_basic_key_generation(self):
        """Generate basic cache key."""
        key = cache_key(42.6977, 23.3219, 6)
        assert key == "42.6977:23.3219:6"
    
    def test_key_rounds_coordinates(self):
        """Coordinates are rounded to 4 decimal places."""
        key = cache_key(42.69771234, 23.32198765, 6)
        assert key == "42.6977:23.322:6"
    
    def test_key_negative_coordinates(self):
        """Negative coordinates are handled."""
        key = cache_key(-33.8688, -151.2093, 12)
        assert key == "-33.8688:-151.2093:12"
    
    def test_key_zero_coordinates(self):
        """Zero coordinates work correctly."""
        key = cache_key(0.0, 0.0, 1)
        assert key == "0.0:0.0:1"


class TestCacheOperations:
    """Tests for cache get/set/clear operations."""
    
    def setup_method(self):
        """Clear cache before each test."""
        cache_clear()
    
    def test_set_and_get(self):
        """Set and retrieve a value."""
        key = cache_key(42.6977, 23.3219, 6)
        data = {"pm25_avg": 12.5, "guidance_text": "Test"}
        
        cache_set(key, data)
        result = cache_get(key)
        
        assert result == data
    
    def test_get_missing_key(self):
        """Get returns None for missing key."""
        result = cache_get("nonexistent:key:1")
        assert result is None
    
    def test_clear_removes_all(self):
        """Clear removes all cached values."""
        cache_set("key1", {"data": 1})
        cache_set("key2", {"data": 2})
        
        cache_clear()
        
        assert cache_get("key1") is None
        assert cache_get("key2") is None
    
    def test_overwrite_existing_key(self):
        """Setting same key overwrites previous value."""
        key = cache_key(42.6977, 23.3219, 6)
        
        cache_set(key, {"version": 1})
        cache_set(key, {"version": 2})
        
        result = cache_get(key)
        assert result["version"] == 2


class TestCacheStats:
    """Tests for cache_stats function."""
    
    def setup_method(self):
        """Clear cache before each test."""
        cache_clear()
    
    def test_empty_cache_stats(self):
        """Stats for empty cache."""
        stats = cache_stats()
        
        assert stats["size"] == 0
        assert stats["maxsize"] > 0
        assert stats["ttl"] > 0
    
    def test_stats_after_adding_items(self):
        """Stats reflect added items."""
        cache_set("key1", {"data": 1})
        cache_set("key2", {"data": 2})
        
        stats = cache_stats()
        assert stats["size"] == 2


class TestCacheThreadSafety:
    """Tests for thread-safe cache operations."""
    
    def setup_method(self):
        """Clear cache before each test."""
        cache_clear()
    
    def test_concurrent_writes(self):
        """Multiple threads can write without errors."""
        errors = []
        
        def write_to_cache(thread_id: int):
            try:
                for i in range(100):
                    key = f"thread{thread_id}:key{i}"
                    cache_set(key, {"thread": thread_id, "index": i})
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=write_to_cache, args=(i,))
            for i in range(5)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
    
    def test_concurrent_reads_and_writes(self):
        """Concurrent reads and writes don't cause errors."""
        errors = []
        cache_set("shared_key", {"initial": True})
        
        def reader():
            try:
                for _ in range(100):
                    cache_get("shared_key")
            except Exception as e:
                errors.append(e)
        
        def writer():
            try:
                for i in range(100):
                    cache_set("shared_key", {"iteration": i})
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=reader),
            threading.Thread(target=reader),
            threading.Thread(target=writer),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0
