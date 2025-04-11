from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os
from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Inicializar banco de dados
def init_db():
    if not os.path.exists('database.db'):
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            expiration_date DATE
        )
        ''')
        
        # Criar admin padrão
        hashed_pw = generate_password_hash('admin123')
        cursor.execute('''
        INSERT INTO users (username, password, is_admin, expiration_date)
        VALUES (?, ?, ?, ?)
        ''', ('admin', hashed_pw, 1, '2099-12-31'))
        
        conn.commit()
        conn.close()

init_db()

# Conexão com o banco de dados
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Rotas principais
@app.route('/')
def home():
    if 'username' in session:
        if session.get('is_admin'):
            return redirect(url_for('admin_panel'))
        return f"Bem-vindo, {session['username']}! Sua conta expira em {session['expiration_date']}"
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['is_admin'] = bool(user['is_admin'])
            session['expiration_date'] = user['expiration_date']
            
            # Verificar se a conta expirou
            if datetime.strptime(user['expiration_date'], '%Y-%m-%d') < datetime.now():
                flash('Sua conta expirou. Entre em contato com o administrador.')
                session.clear()
                return redirect(url_for('login'))
            
            return redirect(url_for('home'))
        else:
            flash('Usuário ou senha inválidos')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Painel administrativo
@app.route('/admin')
def admin_panel():
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    
    return render_template('admin.html', users=users)

@app.route('/admin/create_user', methods=['GET', 'POST'])
def create_user():
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_admin = 1 if request.form.get('is_admin') else 0
        days_valid = int(request.form['days_valid'])
        
        expiration_date = (datetime.now() + timedelta(days=days_valid)).strftime('%Y-%m-%d')
        hashed_pw = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute('''
            INSERT INTO users (username, password, is_admin, expiration_date)
            VALUES (?, ?, ?, ?)
            ''', (username, hashed_pw, is_admin, expiration_date))
            conn.commit()
            flash('Usuário criado com sucesso!')
        except sqlite3.IntegrityError:
            flash('Nome de usuário já existe')
        finally:
            conn.close()
        
        return redirect(url_for('admin_panel'))
    
    return render_template('create_user.html')
        
except sqlite3.IntegrityError as e:
    flash('Nome de usuário já existe')
    print(f"Erro de integridade: {e}") 
if __name__ == '__main__':
    app.run(debug=True)
