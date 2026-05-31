"""
SwiftShip — Crear usuario administrador inicial
Corre UNA sola vez: .venv\\Scripts\\python.exe seed_admin.py
"""

from werkzeug.security import generate_password_hash
from datetime import datetime, timezone
from db.mongo_connector import get_db, Collections

EMAIL    = "admin@swiftship.com"
PASSWORD = "admin1234"
NOMBRE   = "Administrador SwiftShip"

def seed():
    db = get_db()

    if db[Collections.USUARIOS].find_one({'email': EMAIL}):
        print(f"⏭  El admin '{EMAIL}' ya existe.")
        return

    db[Collections.USUARIOS].insert_one({
        'nombre':        NOMBRE,
        'email':         EMAIL,
        'password_hash': generate_password_hash(PASSWORD),
        'rol':           'admin',
        'seller_id':     '',
        'activo':        True,
        'created_at':    datetime.now(timezone.utc)
    })
    print(f"✅ Admin creado: {EMAIL} / {PASSWORD}")
    print("   ⚠️  Cambia la contraseña después del primer login.")

if __name__ == '__main__':
    seed()