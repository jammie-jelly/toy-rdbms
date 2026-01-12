"""Tests for Table class"""
import pytest
from toy import Table, Column


class TestTableBasics:
    def test_create_table(self):
        cols = [Column("id", int), Column("name", str)]
        table = Table("users", cols)
        assert table.name == "users"
        assert "id" in table.columns
        assert "name" in table.columns
        assert table.column_order == ["id", "name"]

    def test_table_starts_empty(self):
        cols = [Column("id", int)]
        table = Table("users", cols)
        assert len(table.rows) == 0

    def test_define_primary_key(self):
        cols = [Column("id", int), Column("name", str)]
        table = Table("users", cols)
        table.define_primary_key("id")
        assert table.pk_column == "id"
        assert "id" in table.unique_columns

    def test_define_primary_key_nonexistent_column(self):
        cols = [Column("id", int)]
        table = Table("users", cols)
        with pytest.raises(ValueError):
            table.define_primary_key("nonexistent")

    def test_define_primary_key_twice_raises(self):
        cols = [Column("id", int)]
        table = Table("users", cols)
        table.define_primary_key("id")
        with pytest.raises(ValueError):
            table.define_primary_key("id")

    def test_add_unique_constraint(self):
        cols = [Column("id", int), Column("email", str)]
        table = Table("users", cols)
        table.add_unique("email")
        assert "email" in table.unique_columns

    def test_add_unique_nonexistent_column(self):
        cols = [Column("id", int)]
        table = Table("users", cols)
        with pytest.raises(ValueError):
            table.add_unique("nonexistent")


class TestTableInsert:
    def test_insert_simple_row(self):
        cols = [Column("id", int), Column("name", str)]
        table = Table("users", cols)
        rowid = table.insert({"id": 1, "name": "Alice"})
        assert rowid == 0
        assert len(table.rows) == 1
        assert table.rows[0] == {"id": 1, "name": "Alice"}

    def test_insert_multiple_rows(self):
        cols = [Column("id", int), Column("name", str)]
        table = Table("users", cols)
        rowid1 = table.insert({"id": 1, "name": "Alice"})
        rowid2 = table.insert({"id": 2, "name": "Bob"})
        assert rowid1 == 0
        assert rowid2 == 1
        assert len(table.rows) == 2

    def test_insert_with_none_values(self):
        cols = [Column("id", int), Column("name", str, nullable=True)]
        table = Table("users", cols)
        rowid = table.insert({"id": 1, "name": None})
        assert table.rows[0]["name"] is None

    def test_insert_not_null_violation(self):
        cols = [Column("id", int, nullable=False)]
        table = Table("users", cols)
        with pytest.raises(ValueError, match="NOT NULL"):
            table.insert({"id": None})

    def test_insert_type_mismatch(self):
        cols = [Column("age", int)]
        table = Table("users", cols)
        with pytest.raises(TypeError, match="Type mismatch"):
            table.insert({"age": "not an int"})

    def test_insert_bool_as_int_rejected(self):
        """Bool should not be accepted as int"""
        cols = [Column("count", int)]
        table = Table("users", cols)
        with pytest.raises(TypeError, match="Type mismatch"):
            table.insert({"count": True})

    def test_insert_autoincrement_pk(self):
        cols = [Column("id", int), Column("name", str)]
        table = Table("users", cols)
        table.define_primary_key("id", autoincrement=True)
        rowid1 = table.insert({"name": "Alice"})
        rowid2 = table.insert({"name": "Bob"})
        assert table.rows[0]["id"] == 1
        assert table.rows[1]["id"] == 2

    def test_insert_explicit_pk_with_autoincrement(self):
        cols = [Column("id", int)]
        table = Table("users", cols)
        table.define_primary_key("id", autoincrement=True)
        table.insert({"id": 10})
        table.insert({})  # Should auto-increment from 10
        assert table.rows[1]["id"] == 11

    def test_insert_pk_unique_violation(self):
        cols = [Column("id", int)]
        table = Table("users", cols)
        table.define_primary_key("id")
        table.insert({"id": 1})
        with pytest.raises(ValueError, match="Unique/PK violation"):
            table.insert({"id": 1})

    def test_insert_unique_constraint_violation(self):
        cols = [Column("id", int), Column("email", str)]
        table = Table("users", cols)
        table.add_unique("email")
        table.insert({"id": 1, "email": "alice@example.com"})
        with pytest.raises(ValueError, match="Unique/PK violation"):
            table.insert({"id": 2, "email": "alice@example.com"})


class TestTableUpdate:
    def test_update_single_row(self):
        cols = [Column("id", int), Column("name", str)]
        table = Table("users", cols)
        table.insert({"id": 1, "name": "Alice"})
        count = table.update({"name": "Alicia"}, lambda r: r["id"] == 1)
        assert count == 1
        assert table.rows[0]["name"] == "Alicia"

    def test_update_multiple_rows(self):
        cols = [Column("id", int), Column("status", str)]
        table = Table("users", cols)
        table.insert({"id": 1, "status": "active"})
        table.insert({"id": 2, "status": "active"})
        count = table.update({"status": "inactive"}, lambda r: r["status"] == "active")
        assert count == 2
        assert all(r["status"] == "inactive" for r in table.rows)

    def test_update_no_where_clause(self):
        cols = [Column("id", int), Column("status", str)]
        table = Table("users", cols)
        table.insert({"id": 1, "status": "active"})
        table.insert({"id": 2, "status": "active"})
        count = table.update({"status": "inactive"})
        assert count == 2

    def test_update_unique_constraint_violation(self):
        cols = [Column("id", int), Column("email", str)]
        table = Table("users", cols)
        table.add_unique("email")
        table.insert({"id": 1, "email": "alice@example.com"})
        table.insert({"id": 2, "email": "bob@example.com"})
        with pytest.raises(ValueError, match="Unique/PK violation"):
            table.update({"email": "alice@example.com"}, lambda r: r["id"] == 2)

    def test_update_own_unique_value_allowed(self):
        cols = [Column("id", int), Column("email", str)]
        table = Table("users", cols)
        table.add_unique("email")
        table.insert({"id": 1, "email": "alice@example.com"})
        count = table.update({"email": "alice@example.com"}, lambda r: r["id"] == 1)
        assert count == 1  # Should not raise


class TestTableDelete:
    def test_delete_single_row(self):
        cols = [Column("id", int), Column("name", str)]
        table = Table("users", cols)
        table.insert({"id": 1, "name": "Alice"})
        table.insert({"id": 2, "name": "Bob"})
        count = table.delete(lambda r: r["id"] == 1)
        assert count == 1
        assert len(table.rows) == 1
        assert table.rows[0]["id"] == 2

    def test_delete_multiple_rows(self):
        cols = [Column("id", int), Column("status", str)]
        table = Table("users", cols)
        table.insert({"id": 1, "status": "inactive"})
        table.insert({"id": 2, "status": "active"})
        table.insert({"id": 3, "status": "inactive"})
        count = table.delete(lambda r: r["status"] == "inactive")
        assert count == 2
        assert len(table.rows) == 1

    def test_delete_all_rows(self):
        cols = [Column("id", int)]
        table = Table("users", cols)
        table.insert({"id": 1})
        table.insert({"id": 2})
        count = table.delete()
        assert count == 2
        assert len(table.rows) == 0

    def test_delete_with_autoincrement_reset(self):
        cols = [Column("id", int)]
        table = Table("users", cols)
        table.define_primary_key("id", autoincrement=True)
        table.insert({})  # id = 1
        table.insert({})  # id = 2
        table.delete()
        assert table._pk_counter == 0
        new_id = table.insert({})
        assert table.rows[0]["id"] == 1  # Resets counter


class TestTableSelect:
    def test_select_all_rows(self):
        cols = [Column("id", int), Column("name", str)]
        table = Table("users", cols)
        table.insert({"id": 1, "name": "Alice"})
        table.insert({"id": 2, "name": "Bob"})
        result = table.select()
        assert len(result) == 2

    def test_select_with_projection(self):
        cols = [Column("id", int), Column("name", str), Column("age", int)]
        table = Table("users", cols)
        table.insert({"id": 1, "name": "Alice", "age": 30})
        result = table.select(proj=["id", "name"])
        assert "age" not in result[0]
        assert "id" in result[0]
        assert "name" in result[0]

    def test_select_with_filter(self):
        cols = [Column("id", int), Column("status", str)]
        table = Table("users", cols)
        table.insert({"id": 1, "status": "active"})
        table.insert({"id": 2, "status": "inactive"})
        result = table.select(where_fn=lambda r: r["status"] == "active")
        assert len(result) == 1
        assert result[0]["id"] == 1

    def test_select_with_order_by_asc(self):
        cols = [Column("id", int), Column("name", str)]
        table = Table("users", cols)
        table.insert({"id": 3, "name": "Charlie"})
        table.insert({"id": 1, "name": "Alice"})
        table.insert({"id": 2, "name": "Bob"})
        result = table.select(order_by=("id", False))
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
        assert result[2]["id"] == 3

    def test_select_with_order_by_desc(self):
        cols = [Column("id", int)]
        table = Table("users", cols)
        table.insert({"id": 1})
        table.insert({"id": 3})
        table.insert({"id": 2})
        result = table.select(order_by=("id", True))
        assert result[0]["id"] == 3
        assert result[1]["id"] == 2
        assert result[2]["id"] == 1

    def test_select_with_limit(self):
        cols = [Column("id", int)]
        table = Table("users", cols)
        for i in range(10):
            table.insert({"id": i})
        result = table.select(limit=3)
        assert len(result) == 3

    def test_select_combined_filters(self):
        cols = [Column("id", int), Column("age", int)]
        table = Table("users", cols)
        for i in range(1, 6):
            table.insert({"id": i, "age": i * 10})
        result = table.select(
            where_fn=lambda r: r["age"] > 25,
            order_by=("age", True),
            limit=2
        )
        assert len(result) == 2
        assert result[0]["age"] == 50
        assert result[1]["age"] == 40

    def test_select_star_projection(self):
        cols = [Column("id", int), Column("name", str)]
        table = Table("users", cols)
        table.insert({"id": 1, "name": "Alice"})
        result = table.select(proj=["*"])
        assert "id" in result[0]
        assert "name" in result[0]

    def test_select_does_not_modify_original(self):
        cols = [Column("id", int)]
        table = Table("users", cols)
        table.insert({"id": 1})
        result = table.select()
        result[0]["id"] = 999
        assert table.rows[0]["id"] == 1
