"""
test_mongo.py
─────────────
Prueba que la conexión a MongoDB funciona correctamente.
Ejecutar con: python test_mongo.py
"""

import sys
sys.path.insert(0, ".")

from db.mongo_connector import get_db, Collections

def test():
    print("Probando conexión a MongoDB...")
    db = get_db()

    # Listar colecciones existentes
    colecciones = db.list_collection_names()
    print(f"Colecciones en la BD: {colecciones if colecciones else '(vacía, es normal)'}")

    # Insertar documento de prueba
    db["test_conexion"].insert_one({"mensaje": "SwiftShip conectado", "ok": True})
    print("Documento de prueba insertado.")

    # Leerlo
    doc = db["test_conexion"].find_one({"ok": True}, {"_id": 0})
    print(f"Documento leído: {doc}")

    # Limpiarlo
    db["test_conexion"].drop()
    print("Colección de prueba eliminada.")

    print("\n✅ MongoDB funciona correctamente.")

if __name__ == "__main__":
    test()