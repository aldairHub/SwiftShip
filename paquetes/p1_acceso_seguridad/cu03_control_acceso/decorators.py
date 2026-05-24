# CU-03: Controlar Acceso por Rol
# Uso: @requiere_login   @requiere_admin   @requiere_vendedor

from functools import wraps
from flask import session, redirect, url_for, flash


def requiere_login(f):
    """Redirige al login si no hay sesión activa."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para continuar.', 'warning')
            return redirect(url_for('login.login'))
        return f(*args, **kwargs)
    return decorated


def requiere_admin(f):
    """Solo permite acceso a usuarios con rol 'admin'."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para continuar.', 'warning')
            return redirect(url_for('login.login'))
        if session.get('rol') != 'admin':
            flash('No tienes permisos para acceder a esta sección.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated


def requiere_vendedor(f):
    """Permite acceso a admin y vendedor (bloquea otros roles)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión para continuar.', 'warning')
            return redirect(url_for('login.login'))
        if session.get('rol') not in ('admin', 'vendedor'):
            flash('Acceso denegado.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated