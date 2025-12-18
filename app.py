from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'superhemmeligkey'

# Funksjon for å lese config fra fil
def load_config(filename):
    config = {}
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line and '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    return config

# Last inn databasekonfigurasjon fra config.n
config = load_config('config.n')

app.config['MYSQL_HOST'] = config.get('MYSQL_HOST')
app.config['MYSQL_USER'] = config.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = config.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = config.get('MYSQL_DB')

mysql = MySQL(app)

# Hjem-siden - viser produkter
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Products")
    products = cur.fetchall()
    cur.close()
    return render_template('nettbutikk.html', products=products)

# Handlekurv (lagres i session)
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = {}
    cart = session['cart']
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    products_in_cart = []
    total = 0
    if cart:
        cur = mysql.connection.cursor()
        for product_id, qty in cart.items():
            cur.execute("SELECT * FROM Products WHERE id=%s", (product_id,))
            product = cur.fetchone()
            if product:
                products_in_cart.append({
                    'id': product[0],
                    'name': product[1],
                    'price': product[3],
                    'quantity': qty,
                    'subtotal': float(product[3]) * qty
                })
                total += float(product[3]) * qty
        cur.close()
    return render_template('cart.html', products=products_in_cart, total=total)

# Enkel checkout (lagrer ordre i DB)
@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('index'))
    cur = mysql.connection.cursor()
    total = 0
    for product_id, qty in cart.items():
        cur.execute("SELECT price FROM Products WHERE id=%s", (product_id,))
        price = cur.fetchone()[0]
        total += float(price) * qty
    # Opprett ordre
    cur.execute("INSERT INTO Orders (user_id, total) VALUES (%s, %s)", (session['user_id'], total))
    order_id = cur.lastrowid
    for product_id, qty in cart.items():
        cur.execute("SELECT price FROM Products WHERE id=%s", (product_id,))
        price = cur.fetchone()[0]
        cur.execute("INSERT INTO OrderItems (order_id, product_id, quantity, price) VALUES (%s,%s,%s,%s)",
                    (order_id, product_id, qty, price))
    mysql.connection.commit()
    session.pop('cart')
    cur.close()
    return "Takk for kjøpet! Ordre registrert."

# Enkel login
@app.route('/login', methods=['GET','POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM Users WHERE username=%s", (username,))
        account = cur.fetchone()
        cur.close()
        if account and account['password_hash'] == password:  # Husk: bruk hash i praksis!
            session['loggedin'] = True
            session['user_id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('index'))
        else:
            msg = 'Feil brukernavn/passord'
    return render_template('login.html', msg=msg)

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

