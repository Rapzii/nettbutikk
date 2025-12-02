from flask import Flask, render_template
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'zaid'          
app.config['MYSQL_PASSWORD'] = 'rapzi@1234' 
app.config['MYSQL_DB'] = 'nettbutikk'

mysql = MySQL(app)

@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Products")
    products = cur.fetchall()
    cur.close()
    return render_template('nettbutikk.html', products=products)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

