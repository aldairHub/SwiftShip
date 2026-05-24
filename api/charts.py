"""
api/charts.py — Endpoints de gráficos usando MongoDB.
Sin filtros: usa colecciones precalculadas (muy rápido).
Con filtros: calcula en vivo sobre pedidos.
"""

import logging
from flask import Blueprint, jsonify, request
from db.mongo_connector import get_db, Collections

logger = logging.getLogger(__name__)
charts_bp = Blueprint("charts", __name__)


def _match(args) -> dict:
    q = {}
    if args.get("country"):   q["country"]  = args["country"]
    if args.get("status"):    q["status"]   = args["status"]
    if args.get("category"):  q["category"] = args["category"]
    if args.get("brand"):     q["brand"]    = args["brand"]
    if args.get("date_from") or args.get("date_to"):
        q["order_date"] = {}
        if args.get("date_from"): q["order_date"]["$gte"] = args["date_from"]
        if args.get("date_to"):   q["order_date"]["$lte"] = args["date_to"]
    return q


def _has_filters(args) -> bool:
    return any(args.get(k) for k in ["country", "status", "category", "brand", "date_from", "date_to"])


@charts_bp.route("/charts", methods=["GET"])
def get_charts():
    try:
        db      = get_db()
        col     = db[Collections.PEDIDOS]
        m       = _match(request.args)
        live    = _has_filters(request.args)

        # ── 1. BARRAS: ingresos por país ──────────────────────────
        if not live:
            d = list(db[Collections.AGG_PAIS].find({}, {"_id": 0}).sort("total_revenue", -1).limit(15))
            bar = {"labels": [x["country"] for x in d], "values": [x["total_revenue"] for x in d]}
        else:
            d = list(col.aggregate([
                {"$match": m},
                {"$group": {"_id": "$country", "total": {"$sum": "$total_amount"}}},
                {"$sort": {"total": -1}}, {"$limit": 15},
            ]))
            bar = {"labels": [x["_id"] for x in d], "values": [round(x["total"], 2) for x in d]}

        # ── 2. LÍNEA: pedidos por mes ─────────────────────────────
        if not live:
            d = list(db[Collections.AGG_SEMANAL].find({}, {"_id": 0}).sort("week", 1).limit(24))
            line = {"labels": [x["week"] for x in d], "values": [x["total_orders"] for x in d]}
        else:
            d = list(col.aggregate([
                {"$match": m},
                {"$group": {"_id": {"$substr": ["$order_date", 0, 7]}, "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}, {"$limit": 24},
            ]))
            line = {"labels": [x["_id"] for x in d], "values": [x["count"] for x in d]}

        # ── 3. PIE: distribución por estado ──────────────────────
        d = list(col.aggregate([
            {"$match": m},
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]))
        pie = {"labels": [x["_id"] for x in d], "values": [x["count"] for x in d]}

        # ── 4. HEATMAP: país × categoría ─────────────────────────
        if not live:
            hm_data = list(db["agg_heatmap"].find({}, {"_id": 0}))
        else:
            hm_data = [
                {"country": x["_id"]["country"], "category": x["_id"]["category"], "count": x["count"]}
                for x in col.aggregate([
                    {"$match": m},
                    {"$group": {"_id": {"country": "$country", "category": "$category"}, "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}}, {"$limit": 300},
                ])
            ]
        countries = sorted(set(d["country"] for d in hm_data))
        cats      = sorted(set(d["category"] for d in hm_data))
        lookup    = {(d["country"], d["category"]): d["count"] for d in hm_data}
        heatmap   = {
            "x": cats,
            "y": countries,
            "z": [[lookup.get((c, cat), 0) for cat in cats] for c in countries],
        }

        # ── 5. SANKEY: país → categoría → estado ─────────────────
        sk_data = list(col.aggregate([
            {"$match": m},
            {"$group": {"_id": {"country": "$country", "category": "$category", "status": "$status"}, "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, {"$limit": 60},
        ]))
        nodes_set = set()
        for d in sk_data:
            nodes_set.update([d["_id"]["country"], d["_id"]["category"], d["_id"]["status"]])
        nodes = [{"id": n, "label": n} for n in nodes_set]
        links = []
        for d in sk_data:
            links.append({"source": d["_id"]["country"],  "target": d["_id"]["category"], "value": d["count"]})
            links.append({"source": d["_id"]["category"], "target": d["_id"]["status"],   "value": d["count"]})
        sankey = {"nodes": nodes, "links": links}

        # ── 6. BUBBLE: métricas por categoría ────────────────────
        if not live:
            d = list(db["agg_bubble"].find({}, {"_id": 0}))
            bubble = d
        else:
            d = list(col.aggregate([
                {"$match": m},
                {"$group": {
                    "_id":               "$category",
                    "avg_quantity":      {"$avg": "$quantity"},
                    "avg_total_amount":  {"$avg": "$total_amount"},
                    "avg_shipping_cost": {"$avg": "$shipping_cost"},
                    "total":             {"$sum": "$total_amount"},
                }},
                {"$sort": {"total": -1}},
            ]))
            max_t = max((x["total"] for x in d), default=1)
            bubble = [{
                "category":          x["_id"],
                "avg_quantity":      round(x["avg_quantity"], 2),
                "avg_total_amount":  round(x["avg_total_amount"], 2),
                "avg_shipping_cost": round(x["avg_shipping_cost"], 2),
                "bubble_size":       round(x["total"] / max_t * 60, 1),
            } for x in d]

        # ── 7. TREEMAP: categoría × marca ─────────────────────────
        if not live:
            treemap = list(db["agg_treemap"].find({}, {"_id": 0}))
        else:
            d = list(col.aggregate([
                {"$match": m},
                {"$group": {"_id": {"category": "$category", "brand": "$brand"}, "total_amount": {"$sum": "$total_amount"}}},
                {"$sort": {"total_amount": -1}}, {"$limit": 80},
            ]))
            treemap = [{"category": x["_id"]["category"], "brand": x["_id"]["brand"], "total_amount": round(x["total_amount"], 2)} for x in d]

        return jsonify({
            "bar_total_amount_by_country":    bar,
            "line_orders_by_week":            line,
            "pie_order_status":               pie,
            "heatmap_country_category":       heatmap,
            "sankey_country_category_status": sankey,
            "bubble_category_metrics":        bubble,
            "treemap_category_brand":         treemap,
        }), 200

    except Exception:
        logger.exception("Error en /api/orders/charts")
        return jsonify({"error": "Internal server error"}), 500


@charts_bp.route("/filters-meta", methods=["GET"])
def filters_meta():
    try:
        col = get_db()[Collections.PEDIDOS]
        return jsonify({
            "countries":       sorted(col.distinct("country")),
            "statuses":        sorted(col.distinct("status")),
            "categories":      sorted(col.distinct("category")),
            "brands":          sorted(col.distinct("brand")),
            "payment_methods": sorted(col.distinct("payment_method")),
        }), 200
    except Exception:
        logger.exception("Error en filters-meta")
        return jsonify({"error": "Internal server error"}), 500