"""
api/crud.py — Endpoints CRUD para colecciones de MongoDB.
"""

import logging
from flask import Blueprint, jsonify, request
from db.mongo_connector import get_db, Collections

logger = logging.getLogger(__name__)
crud_bp = Blueprint("crud", __name__)

# Colecciones permitidas
ALLOWED = {
    "pedidos":      Collections.PEDIDOS,
    "clientes":     Collections.CLIENTES,
    "productos":    Collections.PRODUCTOS,
    "vendedores":   Collections.VENDEDORES,
    "ubicaciones":  Collections.UBICACIONES,
    "categorias":   Collections.CATEGORIAS,
    "marcas":       Collections.MARCAS,
    "metodos_pago": Collections.METODOS_PAGO,
    "estados":      Collections.ESTADOS,
}

ID_FIELDS = {
    "pedidos":      "order_id",
    "clientes":     "customer_id",
    "productos":    "product_id",
    "vendedores":   "seller_id",
    "ubicaciones":  "location_id",
    "categorias":   "name",
    "marcas":       "name",
    "metodos_pago": "name",
    "estados":      "name",
}


def _col(name):
    if name not in ALLOWED:
        return None
    return get_db()[ALLOWED[name]]


# ── LIST ──────────────────────────────────────────────────────────

@crud_bp.route("/<collection>", methods=["GET"])
def list_docs(collection):
    col = _col(collection)
    if col is None:
        return jsonify({"error": f"Colección '{collection}' no existe"}), 404

    page  = max(1, int(request.args.get("page", 1)))
    limit = min(200, int(request.args.get("limit", 50)))
    skip  = (page - 1) * limit
    q     = request.args.get("q", "").strip()

    query = {}
    if q:
        id_field = ID_FIELDS.get(collection, "name")
        query = {"$or": [
            {id_field: {"$regex": q, "$options": "i"}},
            {"name":   {"$regex": q, "$options": "i"}},
        ]}

    total = col.count_documents(query)
    docs  = [{k: v for k, v in d.items() if k != "_id"}
             for d in col.find(query).skip(skip).limit(limit)]

    return jsonify({
        "data":        docs,
        "total":       total,
        "page":        page,
        "total_pages": (total + limit - 1) // limit,
    }), 200


# ── GET ONE ───────────────────────────────────────────────────────

@crud_bp.route("/<collection>/<doc_id>", methods=["GET"])
def get_doc(collection, doc_id):
    col = _col(collection)
    if col is None:
        return jsonify({"error": f"Colección '{collection}' no existe"}), 404

    id_field = ID_FIELDS.get(collection, "name")
    doc = col.find_one({id_field: doc_id}, {"_id": 0})
    if not doc:
        return jsonify({"error": "Documento no encontrado"}), 404
    return jsonify(doc), 200


# ── CREATE ────────────────────────────────────────────────────────

@crud_bp.route("/<collection>", methods=["POST"])
def create_doc(collection):
    col = _col(collection)
    if col is None:
        return jsonify({"error": f"Colección '{collection}' no existe"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400

    result = col.insert_one(data)
    return jsonify({"message": "Creado", "id": str(result.inserted_id)}), 201


# ── UPDATE ────────────────────────────────────────────────────────

@crud_bp.route("/<collection>/<doc_id>", methods=["PUT"])
def update_doc(collection, doc_id):
    col = _col(collection)
    if col is None:
        return jsonify({"error": f"Colección '{collection}' no existe"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON requerido"}), 400

    id_field = ID_FIELDS.get(collection, "name")
    data.pop(id_field, None)
    data.pop("_id", None)

    result = col.update_one({id_field: doc_id}, {"$set": data})
    if result.matched_count == 0:
        return jsonify({"error": "Documento no encontrado"}), 404
    return jsonify({"message": "Actualizado"}), 200


# ── DELETE ────────────────────────────────────────────────────────

@crud_bp.route("/<collection>/<doc_id>", methods=["DELETE"])
def delete_doc(collection, doc_id):
    col = _col(collection)
    if col is None:
        return jsonify({"error": f"Colección '{collection}' no existe"}), 404

    id_field = ID_FIELDS.get(collection, "name")
    result   = col.delete_one({id_field: doc_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Documento no encontrado"}), 404
    return jsonify({"message": "Eliminado"}), 200