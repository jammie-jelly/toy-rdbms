"""Tests for SQL parsing helper functions"""
import pytest
from toy import parse_literal, build_predicate
from sqlglot import parse_one, exp


class TestParseLiteral:
    def test_parse_integer_literal(self):
        sql = parse_one("SELECT 42", dialect="sqlite")
        expr = sql.expressions[0]
        assert parse_literal(expr) == 42

    def test_parse_string_literal(self):
        sql = parse_one("SELECT 'hello'", dialect="sqlite")
        expr = sql.expressions[0]
        assert parse_literal(expr) == "hello"

    def test_parse_float_literal(self):
        sql = parse_one("SELECT 3.14", dialect="sqlite")
        expr = sql.expressions[0]
        assert parse_literal(expr) == 3.14

    def test_parse_non_literal(self):
        expr = parse_one("column_name", dialect="sqlite")
        assert parse_literal(expr) is None


class TestBuildPredicate:
    def test_build_equality_predicate(self):
        sql = parse_one("SELECT * FROM t WHERE id = 42", dialect="sqlite")
        pred = build_predicate(sql.args["where"].this)
        assert pred({"id": 42}) is True
        assert pred({"id": 43}) is False

    def test_build_gt_predicate(self):
        sql = parse_one("SELECT * FROM t WHERE age > 18", dialect="sqlite")
        pred = build_predicate(sql.args["where"].this)
        assert pred({"age": 19}) is True
        assert pred({"age": 18}) is False

    def test_build_lt_predicate(self):
        sql = parse_one("SELECT * FROM t WHERE age < 65", dialect="sqlite")
        pred = build_predicate(sql.args["where"].this)
        assert pred({"age": 64}) is True
        assert pred({"age": 65}) is False

    def test_build_and_predicate(self):
        sql = parse_one("SELECT * FROM t WHERE id = 1 AND status = 'active'", dialect="sqlite")
        pred = build_predicate(sql.args["where"].this)
        assert pred({"id": 1, "status": "active"}) is True
        assert pred({"id": 1, "status": "inactive"}) is False
        assert pred({"id": 2, "status": "active"}) is False

    def test_build_join_predicate(self):
        sql = parse_one("SELECT * FROM users, orders WHERE users.id = orders.user_id", dialect="sqlite")
        table_map = {"users": None, "orders": None}
        result = build_predicate(sql.args["where"].this, table_map)
        assert result == ("JOIN", "users", "id", "orders", "user_id")

    def test_build_complex_and_with_join(self):
        sql = parse_one("SELECT * FROM users, orders WHERE users.id = orders.user_id AND status = 'active'", dialect="sqlite")
        table_map = {"users": None, "orders": None}
        result = build_predicate(sql.args["where"].this, table_map)
        # Result is (join_tuple, [filters])
        assert isinstance(result, tuple)
        assert result[0][0] == "JOIN"
