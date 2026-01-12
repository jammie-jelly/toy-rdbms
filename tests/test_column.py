"""Tests for Column class"""
import pytest
from toy import Column


class TestColumn:
    def test_create_nullable_column(self):
        col = Column("id", int, nullable=True)
        assert col.name == "id"
        assert col.dtype is int
        assert col.nullable is True

    def test_create_not_null_column(self):
        col = Column("email", str, nullable=False)
        assert col.name == "email"
        assert col.dtype is str
        assert col.nullable is False

    def test_default_nullable_is_true(self):
        col = Column("name", str)
        assert col.nullable is True

    def test_column_with_different_types(self):
        col_int = Column("age", int)
        col_str = Column("name", str)
        col_float = Column("price", float)
        col_bool = Column("active", bool)

        assert col_int.dtype is int
        assert col_str.dtype is str
        assert col_float.dtype is float
        assert col_bool.dtype is bool
