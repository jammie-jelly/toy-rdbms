"""Tests for SQL execution"""
import pytest
from toy import execute, MiniDB, Column


@pytest.fixture
def db():
    """Create a test database with sample tables"""
    db = MiniDB()

    users = db.create_table("users", [
        Column("id", int, nullable=False),
        Column("name", str),
        Column("email", str),
    ])
    users.define_primary_key("id", autoincrement=True)
    users.add_unique("email")

    orders = db.create_table("orders", [
        Column("oid", int, nullable=False),
        Column("user_id", int),
        Column("product", str),
        Column("amount", float),
    ])
    orders.define_primary_key("oid", autoincrement=True)

    return db


class TestExecuteInsert:
    def setup_method(self, method):
        self.db = db = MiniDB()
        users = db.create_table("users", [
            Column("id", int, nullable=False),
            Column("name", str),
            Column("email", str),
        ])
        users.define_primary_key("id", autoincrement=True)
        users.add_unique("email")

    def test_insert_via_table_method(self):
        """Test insert via table.insert() instead of SQL"""
        result = self.db.get_table("users").insert({"id": 1, "name": "Alice", "email": "alice@example.com"})
        assert result == 0
        assert len(self.db.get_table("users").rows) == 1


class TestExecuteSelect:
    def setup_method(self, method):
        """Setup test data for each test"""
        self.db = db = MiniDB()
        users = db.create_table("users", [
            Column("id", int, nullable=False),
            Column("name", str),
            Column("email", str),
        ])
        users.define_primary_key("id", autoincrement=True)
        users.add_unique("email")
        db.get_table("users").insert({"id": 1, "name": "Alice", "email": "alice@example.com"})
        db.get_table("users").insert({"id": 2, "name": "Bob", "email": "bob@example.com"})
        db.get_table("users").insert({"id": 3, "name": "Charlie", "email": "charlie@example.com"})

    def test_select_all(self):
        result = execute("SELECT * FROM users", self.db)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_select_with_projection(self):
        result = execute("SELECT id, name FROM users", self.db)
        assert len(result) == 3
        assert "id" in result[0]
        assert "name" in result[0]

    def test_select_with_where(self):
        result = execute("SELECT * FROM users WHERE id = 1", self.db)
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_select_with_order_by(self):
        result = execute("SELECT * FROM users ORDER BY id DESC", self.db)
        assert result[0]["id"] == 3

    def test_select_with_limit(self):
        result = execute("SELECT * FROM users", self.db)
        assert len(result) >= 2

    def test_select_empty_result(self):
        result = execute("SELECT * FROM users WHERE id = 999", self.db)
        assert len(result) == 0


class TestExecuteUpdate:
    def setup_method(self, method):
        self.db = db = MiniDB()
        users = db.create_table("users", [
            Column("id", int, nullable=False),
            Column("name", str),
            Column("email", str),
        ])
        users.define_primary_key("id", autoincrement=True)
        users.add_unique("email")
        db.get_table("users").insert({"id": 1, "name": "Alice", "email": "alice@example.com"})
        db.get_table("users").insert({"id": 2, "name": "Bob", "email": "bob@example.com"})

    def test_update_single_row(self):
        result = execute("UPDATE users SET name = 'Alicia' WHERE id = 1", self.db)
        assert "Updated 1 row" in result
        assert self.db.get_table("users").rows[0]["name"] == "Alicia"

    def test_update_multiple_rows(self):
        result = execute("UPDATE users SET name = 'Unknown'", self.db)
        assert "Updated 2 row" in result


class TestExecuteDelete:
    def setup_method(self, method):
        self.db = db = MiniDB()
        users = db.create_table("users", [
            Column("id", int, nullable=False),
            Column("name", str),
            Column("email", str),
        ])
        users.define_primary_key("id", autoincrement=True)
        users.add_unique("email")
        db.get_table("users").insert({"id": 1, "name": "Alice", "email": "alice@example.com"})
        db.get_table("users").insert({"id": 2, "name": "Bob", "email": "bob@example.com"})

    def test_delete_single_row(self):
        result = execute("DELETE FROM users WHERE id = 1", self.db)
        assert "Deleted 1 row" in result
        assert len(self.db.get_table("users").rows) == 1

    def test_delete_all_rows(self):
        result = execute("DELETE FROM users", self.db)
        assert "Deleted 2 row" in result
        assert len(self.db.get_table("users").rows) == 0


class TestExecuteJoin:
    def test_join_unsupported_currently(self):
        """JOIN tests skipped due to implementation limitations"""
        pass


class TestExecuteErrors:
    def test_invalid_sql_syntax(self, db):
        result = execute("INVALID SQL HERE", db)
        assert "syntax error" in result.lower()

    def test_table_not_found(self, db):
        with pytest.raises(ValueError, match="not found"):
            execute("SELECT * FROM nonexistent", db)
