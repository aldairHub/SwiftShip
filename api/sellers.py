"""
api/sellers.py — Endpoints de vendedores usando MongoDB.
"""

import logging
from flask import Blueprint, jsonify, request
from db.mongo_connector import get_db, Collections

logger = logging.getLogger(__name__)
sellers_bp = Blueprint("sellers", __name__)


@sellers_bp.route("/", methods=["GET"])
def get_sellers():
    try:
        db    = get_db()
        q     = request.args.get("q", "").strip()
        page  = max(1, int(request.args.get("page", 1)))
        limit = min(200, int(request.args.get("limit", 50)))
        skip  = (page - 1) * limit

        query = {}
        if q:
            query = {"$or": [
                {"seller_id": {"$regex": q, "$options": "i"}},
                {"name":      {"$regex": q, "$options": "i"}},
                {"country":   {"$regex": q, "$options": "i"}},
            ]}

        total   = db[Collections.VENDEDORES].count_documents(query)
        sellers = list(db[Collections.VENDEDORES].find(query, {"_id": 0}).skip(skip).limit(limit))

        # Enriquecer con métricas de pedidos
        for seller in sellers:
            sid = seller["seller_id"]
            pipe = [
                {"$match": {"seller_id": sid}},
                {"$group": {
                    "_id":           None,
                    "total_orders":  {"$sum": 1},
                    "total_revenue": {"$sum": "$total_amount"},
                    "cancel_rate":   {"$avg": {"$cond": [{"$eq": ["$status", "Cancelled"]}, 1, 0]}},
                }}
            ]
            metrics = list(db[Collections.PEDIDOS].aggregate(pipe))
            if metrics:
                m = metrics[0]
                seller["total_orders"]  = m["total_orders"]
                seller["total_revenue"] = round(m["total_revenue"], 2)
                seller["cancel_rate"]   = round(m["cancel_rate"] * 100, 1)
            else:
                seller["total_orders"]  = 0
                seller["total_revenue"] = 0
                seller["cancel_rate"]   = 0

        return jsonify({
            "data":        sellers,
            "total":       total,
            "page":        page,
            "total_pages": (total + limit - 1) // limit,
        }), 200
    except Exception:
        logger.exception("Error en GET /api/sellers/")
        return jsonify({"error": "Internal server error"}), 500


@sellers_bp.route("/summary", methods=["GET"])
def sellers_summary():
    try:
        db  = get_db()
        col = db[Collections.VENDEDORES]

        total  = col.count_documents({})
        active = col.count_documents({"active": True})

        avg_r = list(col.aggregate([{"$group": {"_id": None, "avg": {"$avg": "$rating"}}}]))
        avg_rating = round(avg_r[0]["avg"], 2) if avg_r else 0

        top = list(db[Collections.PEDIDOS].aggregate([
            {"$group": {"_id": "$seller_id", "revenue": {"$sum": "$total_amount"}}},
            {"$sort": {"revenue": -1}},
            {"$limit": 1},
        ]))
        top_name = "N/A"
        if top:
            doc = col.find_one({"seller_id": top[0]["_id"]}, {"_id": 0, "name": 1})
            top_name = doc["name"] if doc else "N/A"

        return jsonify({
            "total":      total,
            "active":     active,
            "avg_rating": avg_rating,
            "top_seller": top_name,
        }), 200
    except Exception:
        logger.exception("Error en GET /api/sellers/summary")
        return jsonify({"error": "Internal server error"}), 500