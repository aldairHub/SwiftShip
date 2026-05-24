# CU-04: Cerrar Sesión
# Ruta: GET /auth/logout

from flask import Blueprint, redirect, url_for, session, flash

logout_bp = Blueprint('logout', __name__)


@logout_bp.route('/auth/logout')
def logout():
    nombre = session.get('nombre', 'Usuario')
    session.clear()
    flash(f'Sesión cerrada. Hasta luego, {nombre}.', 'info')
    return redirect(url_for('cu02_login.login'))