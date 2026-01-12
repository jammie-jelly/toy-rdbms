"""Tests for HashIndex class"""
import pytest
from toy import HashIndex


class TestHashIndex:
    def test_add_single_value(self):
        idx = HashIndex()
        idx.add("key1", 0)
        assert idx.lookup("key1") == {0}

    def test_add_multiple_rowids_same_key(self):
        idx = HashIndex()
        idx.add("key1", 0)
        idx.add("key1", 1)
        idx.add("key1", 2)
        assert idx.lookup("key1") == {0, 1, 2}

    def test_lookup_nonexistent_key(self):
        idx = HashIndex()
        assert idx.lookup("nonexistent") == set()

    def test_remove_single_rowid(self):
        idx = HashIndex()
        idx.add("key1", 0)
        idx.add("key1", 1)
        idx.remove("key1", 0)
        assert idx.lookup("key1") == {1}

    def test_remove_last_rowid_cleans_key(self):
        idx = HashIndex()
        idx.add("key1", 0)
        idx.remove("key1", 0)
        assert idx.lookup("key1") == set()
        assert "key1" not in idx.data

    def test_remove_nonexistent_rowid(self):
        idx = HashIndex()
        idx.add("key1", 0)
        idx.remove("key1", 999)  # Should not raise
        assert idx.lookup("key1") == {0}

    def test_lookup_returns_copy(self):
        idx = HashIndex()
        idx.add("key1", 0)
        result = idx.lookup("key1")
        result.add(999)
        assert idx.lookup("key1") == {0}  # Original unchanged

    def test_add_none_value(self):
        idx = HashIndex()
        idx.add(None, 0)
        idx.add(None, 1)
        assert idx.lookup(None) == {0, 1}

    def test_multiple_keys(self):
        idx = HashIndex()
        idx.add("key1", 0)
        idx.add("key2", 1)
        idx.add("key3", 2)
        assert idx.lookup("key1") == {0}
        assert idx.lookup("key2") == {1}
        assert idx.lookup("key3") == {2}
