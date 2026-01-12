"""
MiniRDBMS — Strict feature set complete
- limited data types (int, str, float, bool)
- CRUD operations via basic SQL
- hash-based indexes (PK & UNIQUE)
- single-column primary key (optional auto-increment)
- uniqueness enforcement on insert/update
- simple inner joins via comma syntax + WHERE

Requires: pip install sqlglot==28.5.0
"""

import collections
import typing
import cmd
from dataclasses import dataclass

try:
    from sqlglot import parse_one, exp
    from sqlglot.errors import ParseError
except ImportError:
    print("ERROR: sqlglot is required")
    print("       Run: pip install sqlglot==28.5.0")
    exit(1)

# ──────────────────────────────────────────────────────────────────────────────
#   Core Types & Storage
# ──────────────────────────────────────────────────────────────────────────────

DataValue = typing.Union[int, str, float, bool, None]


class HashIndex:
    """Hash index mapping column value → set of row indices"""
    def __init__(self):
        self.data: dict[DataValue, set[int]] = collections.defaultdict(set)

    def add(self, value: DataValue, rowid: int):
        self.data[value].add(rowid)

    def remove(self, value: DataValue, rowid: int):
        s = self.data.get(value)
        if s:
            s.discard(rowid)
            if not s:
                del self.data[value]

    def lookup(self, value: DataValue) -> set[int]:
        # Defensive copy to prevent external mutation
        return set(self.data.get(value, ()))


@dataclass
class Column:
    """Column schema definition"""
    name: str
    dtype: type
    nullable: bool = True


class Table:
    """In-memory table with optional indexes and constraints"""
    def __init__(self, name: str, columns: list[Column]):
        self.name = name
        self.columns = {c.name: c for c in columns}
        self.column_order = [c.name for c in columns]
        self.rows: list[dict] = []

        self.pk_column: str | None = None
        self.unique_columns: set[str] = set()
        self.indexes: dict[str, HashIndex] = {}

        self._autoincrement_pk = False
        self._pk_counter = 0

    def define_primary_key(self, colname: str, autoincrement: bool = False):
        """Define single-column primary key"""
        if colname not in self.columns:
            raise ValueError(f"Column {colname} does not exist")
        if self.pk_column:
            raise ValueError("Primary key already defined")
        self.pk_column = colname
        self.unique_columns.add(colname)
        self._ensure_index(colname)
        if autoincrement and self.columns[colname].dtype is int:
            self._autoincrement_pk = True

    def add_unique(self, colname: str):
        """Add UNIQUE constraint"""
        if colname not in self.columns:
            raise ValueError(f"Column {colname} does not exist")
        self.unique_columns.add(colname)
        self._ensure_index(colname)

    def _ensure_index(self, colname: str):
        """Create index if missing"""
        if colname not in self.indexes:
            self.indexes[colname] = HashIndex()

    def _check_unique_violation(self, col: str, value: DataValue, exclude_rowid: int | None = None):
        """Validate UNIQUE / PK constraint"""
        if col not in self.unique_columns:
            return
        matches = self.indexes[col].lookup(value)
        if exclude_rowid is not None:
            matches.discard(exclude_rowid)
        if matches:
            raise ValueError(f"Unique/PK violation on {col} = {value!r}")

    def _rebuild_indexes(self):
        """Rebuild all indexes after row compaction"""
        for idx in self.indexes.values():
            idx.data.clear()
        for rowid, row in enumerate(self.rows):
            for col, idx in self.indexes.items():
                idx.add(row.get(col), rowid)

    def insert(self, values_dict: dict) -> int:
        """Insert a single row"""
        row = {c: values_dict.get(c) for c in self.column_order}

        # Auto-increment PK assignment
        if self._autoincrement_pk:
            if values_dict.get(self.pk_column) is None:
                self._pk_counter += 1
                row[self.pk_column] = self._pk_counter
            else:
                self._pk_counter = max(self._pk_counter, values_dict[self.pk_column])

        # NOT NULL + strict type checking
        for k, v in row.items():
            col = self.columns[k]
            if v is None:
                if not col.nullable:
                    raise ValueError(f"NOT NULL column {k} missing value")
                continue
            if col.dtype is int and isinstance(v, bool):
                raise TypeError(f"Type mismatch for {k}: expected int")
            if not isinstance(v, col.dtype):
                raise TypeError(f"Type mismatch for {k}: expected {col.dtype.__name__}")

        rowid = len(self.rows)
        for col in self.unique_columns:
            self._check_unique_violation(col, row.get(col))

        self.rows.append(row)
        for col, idx in self.indexes.items():
            idx.add(row.get(col), rowid)

        return rowid

    def update(self, assignments: dict, where_fn=None) -> int:
        """Update rows matching predicate"""
        count = 0
        for rowid, row in enumerate(self.rows):
            if where_fn is None or where_fn(row):
                for col, new_val in assignments.items():
                    if col in self.unique_columns and new_val != row.get(col):
                        self._check_unique_violation(col, new_val, rowid)

                for col, new_val in assignments.items():
                    old = row[col]
                    row[col] = new_val
                    if col in self.indexes:
                        self.indexes[col].remove(old, rowid)
                        self.indexes[col].add(new_val, rowid)
                count += 1
        return count

    def delete(self, where_fn=None) -> int:
        """Delete rows, rebuilding indexes if partial"""
        if where_fn is None:
            count = len(self.rows)
            self.rows.clear()
            for idx in self.indexes.values():
                idx.data.clear()
            self._pk_counter = 0
            return count

        new_rows = []
        count = 0
        for row in self.rows:
            if where_fn(row):
                count += 1
            else:
                new_rows.append(row)

        self.rows = new_rows
        self._rebuild_indexes()
        return count

    def select(self, proj=None, where_fn=None, order_by=None, limit=None):
        """Select rows with optional projection, filter, order, limit"""
        rows = self.rows
        if where_fn:
            rows = [r for r in rows if where_fn(r)]

        result = (
            [r.copy() for r in rows]
            if proj is None or proj == ["*"]
            else [{c: r.get(c) for c in proj if c in r} for r in rows]
        )

        if order_by:
            col, desc = order_by
            result.sort(key=lambda r: r.get(col), reverse=desc)

        if limit is not None:
            result = result[:limit]

        return result

# ──────────────────────────────────────────────────────────────────────────────
#   SQL Parsing Helpers
# ──────────────────────────────────────────────────────────────────────────────

def parse_literal(expr):
    """Convert SQL literal to Python value"""
    if isinstance(expr, exp.Literal):
        if expr.is_int:
            return int(expr.this)
        if expr.is_number:
            return float(expr.this)
        return expr.this
    return None


def build_predicate(expr, table_map=None):
    """
    Build row filter or detect join condition.
    Returns lambda or ("JOIN", t1, c1, t2, c2)
    """
    if isinstance(expr, exp.EQ):
        left, right = expr.left, expr.right

        # Detect join predicate
        if (
            isinstance(left, exp.Column)
            and isinstance(right, exp.Column)
            and table_map
            and left.table != right.table
            and left.table in table_map
            and right.table in table_map
        ):
            return ("JOIN", left.table, left.name, right.table, right.name)

        val = parse_literal(right)
        if val is not None:
            return lambda r: r.get(left.name) == val

    if isinstance(expr, exp.GT):
        val = parse_literal(expr.right)
        if val is not None:
            return lambda r: r.get(expr.left.name) > val

    if isinstance(expr, exp.LT):
        val = parse_literal(expr.right)
        if val is not None:
            return lambda r: r.get(expr.left.name) < val

    if isinstance(expr, exp.And):
        p1 = build_predicate(expr.left, table_map)
        p2 = build_predicate(expr.right, table_map)

        joins = [p for p in (p1, p2) if isinstance(p, tuple)]
        filters = [p for p in (p1, p2) if callable(p)]

        if joins:
            return joins[0], filters

        return lambda r: all(p(r) for p in filters)

    raise NotImplementedError(f"Condition not supported: {expr}")

# ──────────────────────────────────────────────────────────────────────────────
#   SQL Executor
# ──────────────────────────────────────────────────────────────────────────────

def execute(sql: str, db: 'MiniDB'):
    """Parse and execute a SQL statement"""
    try:
        ast = parse_one(sql.strip(), dialect="sqlite")
    except ParseError as e:
        return f"SQL syntax error: {e}"

    if isinstance(ast, exp.Select):
        tables = [t.name for t in ast.find_all(exp.Table)]
        table_map = {t: db.get_table(t) for t in tables}

        join_info = None
        filter_fn = None

        if ast.args.get("where"):
            pred = build_predicate(ast.args["where"].this, table_map)
            if isinstance(pred, tuple):
                if len(pred) == 2:  # (join_info, filters) from AND expression
                    join_info, filters = pred
                    filter_fn = filters[0] if filters else None
                elif len(pred) == 5:  # ("JOIN", t1, c1, t2, c2) direct join
                    join_info = pred[1:]  # (t1, c1, t2, c2)
                    filter_fn = None
            else:
                filter_fn = pred

        proj = (
            ["*"]
            if any(isinstance(e, exp.Star) for e in ast.expressions)
            else [e.name for e in ast.expressions if isinstance(e, exp.Column)]
        )

        if len(tables) == 1:
            table = table_map[tables[0]]
            order_by = None
            if ast.args.get("order"):
                o = ast.args["order"].expressions[0]
                order_by = (o.this.name, o.args.get("desc") is not None)
            limit = int(ast.args["limit"].args["expression"].this) if ast.args.get("limit") else None
            return table.select(proj if proj != ["*"] else None, filter_fn, order_by, limit)

        if len(tables) == 2 and join_info:
            t1, c1, t2, c2 = join_info
            result = []
            for r1 in table_map[t1].rows:
                if filter_fn and not filter_fn(r1):
                    continue
                for r2 in table_map[t2].rows:
                    if r2.get(c2) == r1.get(c1):
                        row = {f"{t1}.{k}": v for k, v in r1.items()}
                        row.update({f"{t2}.{k}": v for k, v in r2.items()})
                        result.append(row)
            return result

        return "Only single table or simple comma-join supported"

    if isinstance(ast, exp.Insert):
        table = db.get_table(ast.this.this.name)
        columns = [c.name for c in ast.this.expressions] if ast.this.expressions else table.column_order
        for row_values in ast.expression.expressions:
            row = {c: parse_literal(v) for c, v in zip(columns, row_values.expressions)}
            table.insert(row)
        return f"Inserted {len(ast.expression.expressions)} row(s)"

    if isinstance(ast, exp.Update):
        table = db.get_table(ast.this.name)
        assignments = {e.left.name: parse_literal(e.right) for e in ast.expressions}
        where_fn = build_predicate(ast.args["where"].this) if ast.args.get("where") else None
        return f"Updated {table.update(assignments, where_fn)} row(s)"

    if isinstance(ast, exp.Delete):
        table = db.get_table(ast.this.name)
        where_fn = build_predicate(ast.args["where"].this) if ast.args.get("where") else None
        return f"Deleted {table.delete(where_fn)} row(s)"

    return "Unsupported statement type"

# ──────────────────────────────────────────────────────────────────────────────
#   REPL
# ──────────────────────────────────────────────────────────────────────────────

class MiniDB:
    """Database container"""
    def __init__(self):
        self.tables: dict[str, Table] = {}

    def create_table(self, name: str, columns: list[Column]):
        if name in self.tables:
            raise ValueError(f"Table '{name}' already exists")
        self.tables[name] = Table(name, columns)
        return self.tables[name]

    def get_table(self, name: str) -> Table:
        if name not in self.tables:
            raise ValueError(f"Table '{name}' not found")
        return self.tables[name]


class MiniREPL(cmd.Cmd):
    """Interactive shell"""
    intro = "MiniRDBMS — strict feature set complete\n"
    prompt = "mini> "

    def __init__(self, db: MiniDB):
        super().__init__()
        self.db = db

    def do_sql(self, line):
        result = execute(line, self.db)
        if isinstance(result, list):
            if not result:
                print("(empty result)")
                return
            headers = list(result[0].keys())
            print(" | ".join(headers))
            print("-" * len(" | ".join(headers)))
            for r in result:
                print(" | ".join(str(r[h]) for h in headers))
        else:
            print(result)

    def do_quit(self, _):
        return True

    do_exit = do_quit
    do_q = do_quit


if __name__ == "__main__":
    db = MiniDB()

    users = db.create_table("users", [
        Column("id", int, nullable=False),
        Column("email", str, nullable=False),
        Column("name", str),
        Column("age", int),
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

    MiniREPL(db).cmdloop()

