# CU-02: Autenticar Usuario
# Rutas: GET /auth/login  |  POST /auth/login

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from db.mongo_connector import get_db, Collections

login_bp = Blueprint('login', __name__)


@login_bp.route('/auth/login', methods=['GET', 'POST'])
def login():
    if 'usuario_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Por favor completa todos los campos.', 'warning')
            return render_template('p1_acceso/login.html')

        db      = get_db()
        usuario = db[Collections.USUARIOS].find_one({'email': email, 'activo': True})

        if usuario and check_password_hash(usuario['password_hash'], password):
            session['usuario_id'] = str(usuario['_id'])
            session['nombre']     = usuario['nombre']
            session['email']      = usuario['email']
            session['rol']        = usuario['rol']
            session['seller_id']  = usuario.get('seller_id', '')
            flash(f'Bienvenido, {usuario["nombre"]}.', 'success')
            return redirect(url_for('home'))

        flash('Email o contraseña incorrectos.', 'danger')

    return render_template('p1_acceso/login.html')