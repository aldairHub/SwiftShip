# CU-01: Registrar Vendedor
# Rutas: GET /auth/registro  |  POST /auth/registro
# Solo accesible por admin

import random
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from db.mongo_connector import get_db, Collections
from paquetes.p1_acceso_seguridad.cu03_control_acceso.decorators import requiere_admin

registro_bp = Blueprint('registro', __name__)


def _generar_seller_id(db) -> str:
    """Genera un seller_id único con formato SELL + 5 dígitos."""
    while True:
        seller_id = f"SELL{random.randint(10000, 99999)}"
        existe_vendedor = db[Collections.VENDEDORES].find_one({'seller_id': seller_id})
        existe_usuario  = db[Collections.USUARIOS].find_one({'seller_id': seller_id})
        if not existe_vendedor and not existe_usuario:
            return seller_id


@registro_bp.route('/auth/registro', methods=['GET', 'POST'])
@requiere_admin
def registro():
    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        rol      = request.form.get('rol', 'vendedor')

        if not all([nombre, email, password]):
            flash('Todos los campos son obligatorios.', 'warning')
            return render_template('p1_acceso/registro.html')

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'warning')
            return render_template('p1_acceso/registro.html')

        db = get_db()

        if db[Collections.USUARIOS].find_one({'email': email}):
            flash(f'Ya existe un usuario con el email {email}.', 'danger')
            return render_template('p1_acceso/registro.html')

        seller_id = _generar_seller_id(db) if rol == 'vendedor' else ''

        nuevo = {
            'nombre':        nombre,
            'email':         email,
            'password_hash': generate_password_hash(password),
            'rol':           rol,
            'seller_id':     seller_id,
            'activo':        True,
            'created_at':    datetime.now(timezone.utc)
        }

        db[Collections.USUARIOS].insert_one(nuevo)
        # Si es vendedor, crear también su perfil en la colección vendedores
        if rol == 'vendedor':
            from datetime import date
            db[Collections.VENDEDORES].insert_one({
                'seller_id':   seller_id,
                'name':        nombre,
                'email':       email,
                'phone':       '',
                'city':        '',
                'country':     '',
                'rating':      0.0,
                'active':      True,
                'joined_date': date.today().isoformat()
            })

        flash(f'Usuario "{nombre}" creado con rol {rol}. Seller ID: {seller_id or "N/A"}', 'success')
        return redirect(url_for('registro.registro'))

    return render_template('p1_acceso/registro.html')