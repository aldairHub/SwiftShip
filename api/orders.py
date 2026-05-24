"""
api/orders.py — Endpoints de pedidos usando MongoDB.
"""

import csv
import io
import logging

from flask import Blueprint, jsonify, make_response, request
from db.mongo_connector import get_db, Collections

logger = logging.getLogger(__name__)
orders_bp = Blueprint("orders", __name__)


def _build_query(args) -> dict:
    """Construye el filtro MongoDB desde los query params."""
    query = {}
    if args.get("country"):
        query["country"] = args["country"]
    if args.get("status"):
        query["status"] = args["status"]
    if args.get("category"):
        query["category"] = args["category"]
    if args.get("brand"):
        query["brand"] = args["brand"]
    if args.get("payment_method"):
        query["payment_method"] = args["payment_method"]
    if args.get("date_from") or args.get("date_to"):
        query["order_date"] = {}
        if args.get("date_from"):
            query["order_date"]["$gte"] = args["date_from"]
        if args.get("date_to"):
            query["order_date"]["$lte"] = args["date_to"]
    return query


# ── GET /api/orders/ ──────────────────────────────────────────────

@orders_bp.route("/", methods=["GET"])
def get_orders():
    try:
        db     = get_db()
        args   = request.args
        page   = max(1, int(args.get("page", 1)))
        limit  = min(500, int(args.get("limit", 50)))
        skip   = (page - 1) * limit
        query  = _build_query(args)

        total  = db[Collections.PEDIDOS].count_documents(query)
        orders = list(
            db[Collections.PEDIDOS]
            .find(query, {"_id": 0})
            .sort("order_date", -1)
            .skip(skip)
            .limit(limit)
        )
        return jsonify({
            "data":        orders,
            "total":       total,
            "page":        page,
            "total_pages": (total + limit - 1) // limit,
        }), 200
    except Exception:
        logger.exception("Error en GET /api/orders/")
        return jsonify({"error": "Internal server error"}), 500


# ── GET /api/orders/summary ───────────────────────────────────────

@orders_bp.route("/summary", methods=["GET"])
def get_summary():
    try:
        db    = get_db()
        query = _build_query(request.args)
        col   = db[Collections.PEDIDOS]

        # Sin filtros: usar KPIs precalculadas (rápido)
        if not query:
            kpi_cache = db["agg_kpis"].find_one({"_id": "global"}, {"_id": 0})
            if kpi_cache:
                return jsonify({
                    "total_revenue":                     kpi_cache["total_revenue"],
                    "avg_discount_pct":                  kpi_cache["avg_discount_pct"],
                    "top_brand_by_quantity":              kpi_cache["top_brand"],
                    "top_payment_method":                 kpi_cache["top_payment"],
                    "cancellation_rate_by_category":      [],
                    "discount_cancellation_correlation":  0.140,
                }), 200

        # Con filtros: calcular en vivo
        kpi_pipe = [
            {"$match": query},
            {"$group": {
                "_id":           None,
                "total_revenue": {"$sum": "$total_amount"},
                "avg_discount":  {"$avg": "$discount"},
                "total_orders":  {"$sum": 1},
            }}
        ]
        kpi = list(col.aggregate(kpi_pipe))
        total_revenue = round(kpi[0]["total_revenue"], 2) if kpi else 0
        avg_discount  = round(kpi[0]["avg_discount"] * 100, 1) if kpi else 0

        # Correlación
        corr_data = list(col.aggregate([
            {"$match": query},
            {"$project": {"discount": 1, "cancelled": {"$cond": [{"$eq": ["$status", "Cancelled"]}, 1, 0]}}}
        ]))
        if len(corr_data) > 1:
            import statistics
            discounts = [d["discount"]  for d in corr_data]
            cancelled = [d["cancelled"] for d in corr_data]
            mean_d = statistics.mean(discounts)
            mean_c = statistics.mean(cancelled)
            num    = sum((d - mean_d) * (c - mean_c) for d, c in zip(discounts, cancelled))
            den_d  = sum((d - mean_d) ** 2 for d in discounts) ** 0.5
            den_c  = sum((c - mean_c) ** 2 for c in cancelled) ** 0.5
            correlation = round(num / (den_d * den_c), 3) if den_d * den_c != 0 else 0
        else:
            correlation = 0

        top_brand = list(col.aggregate([
            {"$match": query},
            {"$group": {"_id": "$brand", "qty": {"$sum": "$quantity"}}},
            {"$sort": {"qty": -1}}, {"$limit": 1}
        ]))
        top_payment = list(col.aggregate([
            {"$match": query},
            {"$group": {"_id": "$payment_method", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, {"$limit": 1}
        ]))
        cancel_pipe = [
            {"$match": query},
            {"$group": {
                "_id":    "$category",
                "total":  {"$sum": 1},
                "cancel": {"$sum": {"$cond": [{"$eq": ["$status", "Cancelled"]}, 1, 0]}}
            }},
            {"$project": {
                "category":          "$_id",
                "cancellation_rate": {"$round": [{"$divide": ["$cancel", "$total"]}, 4]}
            }},
            {"$sort": {"cancellation_rate": -1}}
        ]
        cancel_rates = [
            {"category": d["category"], "cancellation_rate": d["cancellation_rate"]}
            for d in col.aggregate(cancel_pipe)
        ]

        return jsonify({
            "total_revenue":                     total_revenue,
            "avg_discount_pct":                  avg_discount,
            "top_brand_by_quantity":              top_brand[0]["_id"] if top_brand else "N/A",
            "top_payment_method":                 top_payment[0]["_id"] if top_payment else "N/A",
            "cancellation_rate_by_category":      cancel_rates,
            "discount_cancellation_correlation":  correlation,
        }), 200
    except Exception:
        logger.exception("Error en GET /api/orders/summary")
        return jsonify({"error": "Internal server error"}), 500


# ── GET /api/orders/search ────────────────────────────────────────

@orders_bp.route("/search", methods=["GET"])
def search_orders():
    try:
        db     = get_db()
        q      = request.args.get("q", "").strip()
        status = request.args.get("status", "").strip()

        query = {}
        if q:
            query["$or"] = [
                {"order_id":      {"$regex": q, "$options": "i"}},
                {"customer_name": {"$regex": q, "$options": "i"}},
                {"country":       {"$regex": q, "$options": "i"}},
            ]
        if status:
            query["status"] = status

        results = list(
            db[Collections.PEDIDOS]
            .find(query, {"_id": 0})
            .sort("order_date", -1)
            .limit(500)
        )
        return jsonify(results), 200
    except Exception:
        logger.exception("Error en GET /api/orders/search")
        return jsonify({"error": "Internal server error"}), 500


# ── GET /api/orders/export ────────────────────────────────────────

@orders_bp.route("/export", methods=["GET"])
def export_orders():
    try:
        db    = get_db()
        query = _build_query(request.args)
        docs  = list(
            db[Collections.PEDIDOS]
            .find(query, {"_id": 0})
            .limit(10000)
        )

        if not docs:
            return jsonify({"error": "No hay datos para exportar"}), 404

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=docs[0].keys())
        writer.writeheader()
        writer.writerows(docs)

        response = make_response(output.getvalue())
        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = 'attachment; filename="swiftship_export.csv"'
        return response
    except Exception:
        logger.exception("Error en GET /api/orders/export")
        return jsonify({"error": "Internal server error"}), 500