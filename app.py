from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import ForeignKey, Integer, Float, DateTime
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import relationship
from flask import render_template
import requests
from bs4 import BeautifulSoup
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:password@localhost/python_learning_path'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=30)  # Set session lifetime to 30 minutes
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    hashed_password = db.Column(db.String(100), nullable=False)


class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
class Clients(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    productname = db.Column(db.String(255), nullable=False)
    productunit = db.Column(db.String(255), nullable=False)
class SalesOrders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, ForeignKey('clients.id'), nullable=False)
    product_id = db.Column(db.Integer, ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = relationship('Clients', backref='sales_orders', foreign_keys=[client_id])
    product = relationship('Products', backref='sales_orders', foreign_keys=[product_id])
    item_details = db.relationship('ItemDetailsSalesOrder', backref='sales_order_rel', lazy=True)

class ItemDetailsSalesOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    
    sales_order = db.relationship('SalesOrders', backref='item_details_rel', lazy=True)
    product = db.relationship('Products', backref=db.backref('item_details', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Middleware to update user's last activity time on each request
@app.before_request
def update_last_activity():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


# Logout user if inactive for more than the session lifetime
@login_manager.unauthorized_handler
def unauthorized():
    flash('You were logged out due to inactivity.', 'info')
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.hashed_password, password):
            login_user(user, remember=True)  # Set remember to True to use the permanent session lifetime
            flash('Login successful.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check your username and password.', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(username=username, hashed_password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully. You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']

#         user = User.query.filter_by(username=username).first()

#         if user and bcrypt.check_password_hash(user.hashed_password, password):
#             login_user(user, remember=True)  # Set remember to True to use the permanent session lifetime
#             flash('Login successful.', 'success')
#             return redirect(url_for('index'))
#         else:
#             flash('Login unsuccessful. Please check your username and password.', 'danger')

#     return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/viewclients')
@login_required
def viewclients():
    clients_data = Clients.query.all()
    return render_template('viewclients.html', clients_data=clients_data)

@app.route('/add_client', methods=['POST'])
def add_client():
    name = request.form['name']
    address = request.form['address']
    email = request.form['email']
    phone = request.form['phone']

    new_client = Clients(name=name,address=address, email=email, phone=phone)
    db.session.add(new_client)
    db.session.commit()

    return redirect(url_for('viewclients'))

@app.route('/delete_client/<int:client_id>')
def delete_client(client_id):
    client = Clients.query.get(client_id)
    db.session.delete(client)
    db.session.commit()

    return redirect(url_for('viewclients'))

@app.route('/edit_client/<int:client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    client = Clients.query.get(client_id)

    if request.method == 'POST':
        client.name = request.form['name']
        client.address = request.form['address']
        client.email = request.form['email']
        client.phone = request.form['phone']

        db.session.commit()
        return redirect(url_for('viewclients'))

    return render_template('edit_client.html', client=client)


@app.route('/viewproducts')
def viewproducts():
    products_data = Products.query.all()
    return render_template('viewproducts.html', products_data=products_data)

@app.route('/add_product', methods=['POST'])
def add_product():
    productname = request.form['productname']
    productuni = request.form['productunit']
    new_product = Products(productname=productname, productunit=productuni)
    
    db.session.add(new_product)
    db.session.commit()

    return redirect(url_for('viewproducts'))

@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    product = Products.query.get(product_id)
    db.session.delete(product)
    db.session.commit()

    return redirect(url_for('viewproducts'))

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Products.query.get(product_id)

    if request.method == 'POST':
        product.productname = request.form['productname']
        product.productunit = request.form['productunit']
        

        db.session.commit()
        return redirect(url_for('viewproducts'))

    return render_template('edit_product.html', product=product)

@app.route('/view_sales_orders')
def view_sales_orders():
    clients_data = Clients.query.all()
    products_data = Products.query.all()
    sales_orders_data = SalesOrders.query.options(joinedload(SalesOrders.client), joinedload(SalesOrders.product)).all()

    return render_template(
        'view_sales_orders.html',
        clients_data=clients_data,
        products_data=products_data,
        sales_orders_data=sales_orders_data
    )

@app.route('/add_sales_order', methods=['POST'])
def add_sales_order():
    client_id = request.form['client_id']
    product_ids = request.form.getlist('products[]')  # Ensure this matches the name in your HTML form
    quantities = request.form.getlist('quantities[]')
    rates = request.form.getlist('rates[]')
    amounts = request.form.getlist('amounts[]')

    for product_id, quantity, rate, amount in zip(product_ids, quantities, rates, amounts):
        new_sales_order = SalesOrders(
            client_id=client_id,
            product_id=product_id,
            quantity=quantity,
            rate=rate,
            amount=amount
        )
        db.session.add(new_sales_order)

    db.session.commit()

    return redirect(url_for('view_sales_orders'))


# Add a method to convert Products instances to a serializable format
def serialize_product(product):
    return {
        'id': product.id,
        'productname': product.productname,
        'productunit': product.productunit,
    }

# Update the route for getting products to use the new serialization method
@app.route('/get_products')
def get_products():
    products_data = Products.query.all()
    serialized_products = [serialize_product(product) for product in products_data]
    return jsonify(products=serialized_products)

@app.route('/edit_sales_order/<int:sales_order_id>', methods=['GET', 'POST'])
def edit_sales_order(sales_order_id):
    sales_order = SalesOrders.query.get(sales_order_id)

    if request.method == 'POST':
        sales_order.client_id = request.form['client_id']
        sales_order.product_id = request.form['product_id']
        sales_order.quantity = request.form['quantity']
        sales_order.rate = request.form['rate']
        sales_order.amount = request.form['amount']

        db.session.commit()
        return redirect(url_for('view_sales_orders'))

    clients_data = Clients.query.all()
    products_data = Products.query.all()

    return render_template('edit_sales_order.html', sales_order=sales_order, clients_data=clients_data, products_data=products_data)


@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if request.method == 'POST':
        url = request.form['url']
        
        # Fetch the web page content
        response = requests.get(url)
        if response.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the content you want (customize as needed)
            scraped_content = soup.get_text()

            # Render the template with the scraped content
            return render_template('scrape_result.html', url=url, scraped_content=scraped_content)

        # Handle invalid URLs or other errors
        return render_template('scrape_result.html', url=url, error='Failed to fetch content. Please check the URL.')

    # Render the form to enter the URL
    return render_template('scrape_form.html')


@app.route('/learning')
def learning():
    # Fetch data from the database
    modules_data = Module.query.all()

    # Render the HTML template with the fetched data
    return render_template('learning.html', modules_data=modules_data)

@app.route('/')
@login_required
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)