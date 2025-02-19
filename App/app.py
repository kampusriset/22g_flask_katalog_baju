# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import (
    get_all_products,
    add_product,
    get_product_by_id,
    update_product,
    delete_product,
    get_dashboard_stats,
    create_admin,
    get_admin_by_username,
    reset_password,
    get_db_connection,
    get_products_paginated,
    search_products
)
from werkzeug.security import check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo
from flask import abort

app = Flask(__name__)
app.secret_key = 'your_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, admin_id, username):
        self.id = admin_id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM admin WHERE admin_id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['admin_id'], user['username'])
    return None

@login_manager.unauthorized_handler
def unauthorized():
    flash('You need to log in to access this page.', 'warning')
    return redirect(url_for('login'))

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ResetPasswordForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

@app.route('/')
@login_required
def index():
    query = request.args.get('search', '')  # Mendapatkan query pencarian dari query string
    page = request.args.get('page', 1, type=int)  # Mendapatkan nomor halaman dari query string
    per_page = 5  # Jumlah produk per halaman

    if query:
        products = search_products(query, page, per_page)
        # Menghitung total produk yang cocok dengan pencarian
        conn = get_db_connection()
        total_products = conn.execute(
            'SELECT COUNT(*) FROM produk WHERE nama_produk LIKE ? OR deskripsi LIKE ?',
            ('%' + query + '%', '%' + query + '%')
        ).fetchone()[0]
        conn.close()
    else:
        products = get_products_paginated(page, per_page)
        # Menghitung total produk untuk pagination
        conn = get_db_connection()
        total_products = conn.execute('SELECT COUNT(*) FROM produk').fetchone()[0]
        conn.close()

    total_pages = (total_products + per_page - 1) // per_page  # Menghitung total halaman

    return render_template('index.html', products=products, page=page, total_pages=total_pages, search=query)

@app.route('/dashboard')
@login_required
def dashboard():
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product_route():
    if request.method == 'POST':
        nama_produk = request.form['nama_produk']
        deskripsi = request.form['deskripsi']
        harga = request.form['harga']
        stok = request.form['stok']
        admin_id = 1  # Misalkan admin_id adalah 1 untuk contoh ini
        add_product(nama_produk, deskripsi, harga, stok, admin_id)
        return redirect(url_for('index'))
    return render_template('add_product.html')

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM produk WHERE produk_id = ?', (product_id,)).fetchone()
    
    if request.method == 'POST':
        # Ambil data dari form
        nama_produk = request.form['nama_produk']
        deskripsi = request.form['deskripsi']
        harga = request.form['harga']
        stok = request.form['stok']
        
        # Update produk di database
        conn.execute('UPDATE produk SET nama_produk = ?, deskripsi = ?, harga = ?, stok = ? WHERE produk_id = ?',
                     (nama_produk, deskripsi, harga, stok, product_id))
        conn.commit()
        conn.close()
        flash('Produk berhasil diperbarui!', 'success')
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:produk_id>', methods=['POST'])
def delete_product_route(produk_id):
    delete_product(produk_id)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        create_admin(form.username.data, form.password.data, form.email.data)
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        admin = get_admin_by_username(form.username.data)
        if admin and check_password_hash(admin['password'], form.password.data):
            user = User(admin['admin_id'], admin['username'])
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password_route():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        reset_password(form.username.data, form.new_password.data)
        flash('Password has been reset!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)