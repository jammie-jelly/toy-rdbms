from bottle import Bottle, run, request, redirect, template
from toy import MiniDB, Column, execute

app = Bottle()
db = MiniDB()

# ─── Setup tables ─────────────────────────────
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

# ─── Routes ──────────────────────────────────

@app.route('/')
def index():
    return template('''
        <h2>Dashboard</h2>
        <a href="/users">Manage Users</a> |
        <a href="/orders">Manage Orders</a> |
        <a href="/orders/join">Orders with Users</a>
    ''')

# ─── Users ───────────────────────────────────
@app.route('/users')
def list_users():
    rows = execute("SELECT * FROM users", db)
    return template('''
        <h2>Users</h2>
        <a href="/users/add">Add User</a> | <a href="/">Back</a>
        <table border="1" cellpadding="5">
            <tr><th>ID</th><th>Email</th><th>Name</th><th>Age</th><th>Actions</th></tr>
            % for u in rows:
                <tr>
                    <td>{{u["id"]}}</td>
                    <td>{{u["email"]}}</td>
                    <td>{{u["name"]}}</td>
                    <td>{{u["age"]}}</td>
                    <td>
                        <a href="/users/edit/{{u['id']}}">Edit</a> |
                        <a href="/users/delete/{{u['id']}}">Delete</a>
                    </td>
                </tr>
            % end
        </table>
    ''', rows=rows)

@app.route('/users/add', method=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        email = request.forms.get('email')
        name = request.forms.get('name')
        age = request.forms.get('age')
        age = int(age) if age else None
        execute(f"INSERT INTO users (email, name, age) VALUES ('{email}', '{name}', {age})", db)
        redirect('/users')
    return '''
        <h2>Add User</h2>
        <form method="post">
            Email: <input name="email"><br>
            Name: <input name="name"><br>
            Age: <input name="age"><br>
            <input type="submit" value="Add">
        </form>
        <a href="/users">Back</a>
    '''

@app.route('/users/edit/<uid:int>', method=['GET', 'POST'])
def edit_user(uid):
    if request.method == 'POST':
        email = request.forms.get('email')
        name = request.forms.get('name')
        age = request.forms.get('age')
        age = int(age) if age else None
        execute(f"UPDATE users SET email='{email}', name='{name}', age={age} WHERE id={uid}", db)
        redirect('/users')
    user = execute(f"SELECT * FROM users WHERE id={uid}", db)[0]
    return template('''
        <h2>Edit User</h2>
        <form method="post">
            Email: <input name="email" value="{{user['email']}}"><br>
            Name: <input name="name" value="{{user['name']}}"><br>
            Age: <input name="age" value="{{user['age']}}"><br>
            <input type="submit" value="Update">
        </form>
        <a href="/users">Back</a>
    ''', user=user)

@app.route('/users/delete/<uid:int>')
def delete_user(uid):
    execute(f"DELETE FROM users WHERE id={uid}", db)
    redirect('/users')

# ─── Orders ──────────────────────────────────
@app.route('/orders')
def list_orders():
    rows = execute("SELECT * FROM orders", db)
    return template('''
        <h2>Orders</h2>
        <a href="/orders/add">Add Order</a> | <a href="/">Back</a>
        <table border="1" cellpadding="5">
            <tr><th>OID</th><th>User ID</th><th>Product</th><th>Amount</th><th>Actions</th></tr>
            % for o in rows:
                <tr>
                    <td>{{o["oid"]}}</td>
                    <td>{{o["user_id"]}}</td>
                    <td>{{o["product"]}}</td>
                    <td>{{o["amount"]}}</td>
                    <td>
                        <a href="/orders/edit/{{o['oid']}}">Edit</a> |
                        <a href="/orders/delete/{{o['oid']}}">Delete</a>
                    </td>
                </tr>
            % end
        </table>
    ''', rows=rows)

@app.route('/orders/add', method=['GET', 'POST'])
def add_order():
    if request.method == 'POST':
        user_id = int(request.forms.get('user_id'))
        product = request.forms.get('product')
        amount = float(request.forms.get('amount'))
        execute(f"INSERT INTO orders (user_id, product, amount) VALUES ({user_id}, '{product}', {amount})", db)
        redirect('/orders')
    users_list = execute("SELECT id, name FROM users", db)
    return template('''
        <h2>Add Order</h2>
        <form method="post">
            User:
            <select name="user_id">
                % for u in users:
                    <option value="{{u['id']}}">{{u['id']}} - {{u['name']}}</option>
                % end
            </select><br>
            Product: <input name="product"><br>
            Amount: <input name="amount"><br>
            <input type="submit" value="Add">
        </form>
        <a href="/orders">Back</a>
    ''', users=users_list)

@app.route('/orders/edit/<oid:int>', method=['GET', 'POST'])
def edit_order(oid):
    if request.method == 'POST':
        user_id = int(request.forms.get('user_id'))
        product = request.forms.get('product')
        amount = float(request.forms.get('amount'))
        execute(f"UPDATE orders SET user_id={user_id}, product='{product}', amount={amount} WHERE oid={oid}", db)
        redirect('/orders')
    order = execute(f"SELECT * FROM orders WHERE oid={oid}", db)[0]
    users_list = execute("SELECT id, name FROM users", db)
    return template('''
        <h2>Edit Order</h2>
        <form method="post">
            User:
            <select name="user_id">
                % for u in users:
                    <option value="{{u['id']}}" {{'selected' if u['id']==order['user_id'] else ''}}>
                        {{u['id']}} - {{u['name']}}
                    </option>
                % end
            </select><br>
            Product: <input name="product" value="{{order['product']}}"><br>
            Amount: <input name="amount" value="{{order['amount']}}"><br>
            <input type="submit" value="Update">
        </form>
        <a href="/orders">Back</a>
    ''', order=order, users=users_list)

@app.route('/orders/delete/<oid:int>')
def delete_order(oid):
    execute(f"DELETE FROM orders WHERE oid={oid}", db)
    redirect('/orders')

# ─── Join view ────────────────────────────────
@app.route('/orders/join')
def orders_with_users():
    rows = execute("SELECT * FROM users, orders WHERE users.id = orders.user_id", db)
    return template('''
        <h2>Orders with Users</h2>
        <a href="/">Back</a>
        <table border="1" cellpadding="5">
            <tr>
                <th>Order ID</th><th>User</th><th>Email</th><th>Product</th><th>Amount</th>
            </tr>
            % for r in rows:
                <tr>
                    <td>{{r['orders.oid']}}</td>
                    <td>{{r['users.name']}}</td>
                    <td>{{r['users.email']}}</td>
                    <td>{{r['orders.product']}}</td>
                    <td>{{r['orders.amount']}}</td>
                </tr>
            % end
        </table>
    ''', rows=rows)

# ─── Run ─────────────────────────────────────
if __name__ == '__main__':
    run(app, host='localhost', port=8080, debug=True)
