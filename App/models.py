# models.py
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def get_db_connection():
    conn = sqlite3.connect('katalog_produk.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM produk').fetchall()
    conn.close()
    return products

def get_products_paginated(page, per_page):
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM produk LIMIT ? OFFSET ?', (per_page, (page - 1) * per_page)).fetchall()
    conn.close()
    return products

def search_products(query, page, per_page):
    conn = get_db_connection()
    products = conn.execute(
        'SELECT * FROM produk WHERE nama_produk LIKE ? OR deskripsi LIKE ? LIMIT ? OFFSET ?',
        ('%' + query + '%', '%' + query + '%', per_page, (page - 1) * per_page)
    ).fetchall()
    conn.close()
    return products

def add_product(nama_produk, deskripsi, harga, stok, admin_id):
    conn = get_db_connection()
    conn.execute('INSERT INTO produk (nama_produk, deskripsi, harga, stok, admin_id) VALUES (?, ?, ?, ?, ?)',
                 (nama_produk, deskripsi, harga, stok, admin_id))
    conn.commit()
    conn.close()

def get_product_by_id(produk_id):
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM produk WHERE produk_id = ?', (produk_id,)).fetchone()
    conn.close()
    return product

def update_product(produk_id, nama_produk, deskripsi, harga, stok):
    conn = get_db_connection()
    conn.execute('UPDATE produk SET nama_produk = ?, deskripsi = ?, harga = ?, stok = ? WHERE produk_id = ?',
                 (nama_produk, deskripsi, harga, stok, produk_id))
    conn.commit()
    conn.close()

def delete_product(produk_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM produk WHERE produk_id = ?', (produk_id,))
    conn.commit()
    conn.close()

def get_dashboard_stats():
    conn = get_db_connection()
    total_products = conn.execute('SELECT COUNT(*) FROM produk').fetchone()[0]
    total_stock = conn.execute('SELECT SUM(stok) FROM produk').fetchone()[0] or 0
    total_revenue = conn.execute('SELECT SUM(harga * stok) FROM produk').fetchone()[0] or 0
    conn.close()
    return {
        'total_products': total_products,
        'total_stock': total_stock,
        'total_revenue': total_revenue
    }

def create_admin(username, password, email):
    conn = get_db_connection()
    hashed_password = generate_password_hash(password)
    conn.execute('INSERT INTO admin (username, password, email) VALUES (?, ?, ?)',
                 (username, hashed_password, email))
    conn.commit()
    conn.close()

def get_admin_by_username(username):
    conn = get_db_connection()
    admin = conn.execute('SELECT * FROM admin WHERE username = ?', (username,)).fetchone()
    conn.close()
    return admin

def reset_password(username, new_password):
    conn = get_db_connection()
    hashed_password = generate_password_hash(new_password)
    conn.execute('UPDATE admin SET password = ? WHERE username = ?', (hashed_password, username))
    conn.commit()
    conn.close()