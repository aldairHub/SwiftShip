"""
db/mongo_connector.py
─────────────────────
Maneja la conexión a MongoDB para SwiftShip.
"""

import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure


# ── Nombres de colecciones ─────────────────────────────────────────
class Collections:
    # Hechos
    PEDIDOS       = "pedidos"
    # Dimensiones
    CLIENTES      = "clientes"
    PRODUCTOS     = "productos"
    VENDEDORES    = "vendedores"
    UBICACIONES   = "ubicaciones"
    CATEGORIAS    = "categorias"
    MARCAS        = "marcas"
    METODOS_PAGO  = "metodos_pago"
    ESTADOS       = "estados_pedido"
    # Agregaciones
    AGG_PAIS      = "agg_ventas_pais"
    AGG_CATEGORIA = "agg_ventas_categoria"
    AGG_SEMANAL   = "agg_ventas_semanal"
    # Seguridad
    USUARIOS      = "usuarios"


# ── Cliente global ─────────────────────────────────────────────────
_client = None
_db     = None


def get_db():
    """Retorna la base de datos. Crea la conexión si no existe."""
    global _client, _db

    if _db is not None:
        return _db

    uri  = os.getenv("MONGO_URI", "mongodb://admin:admin@localhost:27017/swiftship?authSource=admin")
    name = os.getenv("MONGO_DB", "swiftship")

    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client[name]
        print(f"[MongoDB] Conectado a '{name}'.")
    except ConnectionFailure as e:
        print(f"[MongoDB] Error de conexión: {e}")
        raise

    return _db


def create_indexes():
    """Crea los índices necesarios en todas las colecciones."""
    db = get_db()

    db[Collections.PEDIDOS].create_index([("order_id", ASCENDING)], unique=True)
    db[Collections.PEDIDOS].create_index([("order_date", DESCENDING)])
    db[Collections.PEDIDOS].create_index([("status", ASCENDING)])
    db[Collections.PEDIDOS].create_index([("country", ASCENDING)])
    db[Collections.PEDIDOS].create_index([("category", ASCENDING)])
    db[Collections.PEDIDOS].create_index([("seller_id", ASCENDING)])

    db[Collections.CLIENTES].create_index([("customer_id", ASCENDING)], unique=True)
    db[Collections.PRODUCTOS].create_index([("product_id", ASCENDING)], unique=True)
    db[Collections.VENDEDORES].create_index([("seller_id", ASCENDING)], unique=True)
    db[Collections.USUARIOS].create_index([("email", ASCENDING)], unique=True)

    print("[MongoDB] Índices creados.")