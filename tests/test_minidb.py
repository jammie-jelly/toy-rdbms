"""Tests for MiniDB class"""
import pytest
from toy import MiniDB, Table, Column


class TestMiniDB:
    def test_create_table(self):
        db = MiniDB()
        cols = [Column("id", int), Column("name", str)]
        table = db.create_table("users", cols)
        assert table.name == "users"
        assert "users" in db.tables

    def test_get_existing_table(self):
        db = MiniDB()
        cols = [Column("id", int)]
        table = db.create_table("users", cols)
        retrieved = db.get_table("users")
        assert retrieved is table

    def test_get_nonexistent_table(self):
        db = MiniDB()
        with pytest.raises(ValueError, match="not found"):
            db.get_table("nonexistent")

    def test_create_duplicate_table(self):
        db = MiniDB()
        cols = [Column("id", int)]
        db.create_table("users", cols)
        with pytest.raises(ValueError, match="already exists"):
            db.create_table("users", cols)

    def test_multiple_tables(self):
        db = MiniDB()
        cols1 = [Column("id", int)]
        cols2 = [Column("oid", int)]
        db.create_table("users", cols1)
        db.create_table("orders", cols2)
        assert len(db.tables) == 2
        assert "users" in db.tables
        assert "orders" in db.tables
