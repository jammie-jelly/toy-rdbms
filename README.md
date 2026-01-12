# toy-rdbms
relational database management system demo

Requirements:
- Python 3.x
- sqlglot==28.5.0
- Bottle.py (current version - 0.14-dev)

Usage:

- `python toy.py`
(Prepend `sql` before query)


```
-- Insert users
INSERT INTO users (email, name, age) VALUES ('alice@example.com', 'Alice', 30);
INSERT INTO users (email, name, age) VALUES ('bob@example.com', 'Bob', 25);
INSERT INTO users (email, name, age) VALUES ('carol@example.com', 'Carol', 28);

-- Insert orders
INSERT INTO orders (user_id, product, amount) VALUES (1, 'Book', 12.5);
INSERT INTO orders (user_id, product, amount) VALUES (1, 'Pen', 1.5);
INSERT INTO orders (user_id, product, amount) VALUES (2, 'Notebook', 5.0);
INSERT INTO orders (user_id, product, amount) VALUES (3, 'Bag', 20.0);

-- Select all users
SELECT * FROM users;

-- Select specific columns
SELECT name, age FROM users;

-- Filtered select
SELECT * FROM users WHERE age > 26;

-- Update a user
UPDATE users SET age = 31 WHERE name = 'Alice';

-- Delete a user
DELETE FROM users WHERE name = 'Bob';

-- Join users with orders
SELECT users.name, orders.product, orders.amount
FROM users, orders
WHERE users.id = orders.user_id;

-- Order by age descending
SELECT name, age FROM users ORDER BY age DESC;

-- Limit results
SELECT * FROM orders LIMIT 2;

-- Test unique constraint violation (should error)
INSERT INTO users (email, name, age) VALUES ('alice@example.com', 'Alice2', 22);
```

Type `exit` to quit.

- For web CRUD demo:
 `python web.py` then open in browser `http://locahost:8080`