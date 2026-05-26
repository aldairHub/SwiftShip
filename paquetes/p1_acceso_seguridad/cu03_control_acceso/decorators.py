# CU-03: Controlar Acceso por Rol
# Decoradores: @requiere_login  @requiere_admin  @requiere_vendedor

from functools import wraps
from flask import session, redirect, url_for, flash, request


def requiere_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            session['next_url'] = request.url
            flash('Debes iniciar sesión para continuar.', 'warning')
            return redirect(url_for('login.login'))
        return f(*args, **kwargs)
    return decorated


def requiere_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            session['next_url'] = request.url
            flash('Debes iniciar sesión para continuar.', 'warning')
            return redirect(url_for('login.login'))
        if session.get('rol') != 'admin':
            flash('No tienes permisos para acceder a esta sección.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated


def requiere_vendedor(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            session['next_url'] = request.url
            flash('Debes iniciar sesión para continuar.', 'warning')
            return redirect(url_for('login.login'))
        if session.get('rol') not in ('admin', 'vendedor'):
            flash('Acceso denegado.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated