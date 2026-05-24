"""
etl/pipeline_agg.py
────────────────────
Construye las colecciones de agregación precalculadas en MongoDB.
Se puede ejecutar independientemente después del ETL principal.
"""

import sys
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

from pymongo import UpdateOne
from db.mongo_connector import get_db, Collections


def build_aggregations():
    db  = get_db()
    col = db[Collections.PEDIDOS]

    print("[Agg] Construyendo agregaciones precalculadas...")

    # ── Ventas por país ───────────────────────────────────────────
    pipe_pais = [
        {"$group": {
            "_id":           "$country",
            "total_revenue": {"$sum": "$total_amount"},
            "total_orders":  {"$sum": 1},
            "avg_discount":  {"$avg": "$discount"},
        }},
        {"$sort": {"total_revenue": -1}},
    ]
    pais_data = list(col.aggregate(pipe_pais))
    ops = [
        UpdateOne(
            {"country": d["_id"]},
            {"$set": {
                "country":       d["_id"],
                "total_revenue": round(d["total_revenue"], 2),
                "total_orders":  d["total_orders"],
                "avg_discount":  round(d["avg_discount"], 4),
            }},
            upsert=True
        )
        for d in pais_data
    ]
    db[Collections.AGG_PAIS].bulk_write(ops)
    print(f"  [+] agg_ventas_pais: {len(ops)} países")

    # ── Ventas por categoría ──────────────────────────────────────
    pipe_cat = [
        {"$group": {
            "_id":          "$category",
            "total_revenue":{"$sum": "$total_amount"},
            "total_orders": {"$sum": 1},
            "avg_order":    {"$avg": "$total_amount"},
        }},
        {"$sort": {"total_revenue": -1}},
    ]
    cat_data = list(col.aggregate(pipe_cat))
    ops = [
        UpdateOne(
            {"category": d["_id"]},
            {"$set": {
                "category":      d["_id"],
                "total_revenue": round(d["total_revenue"], 2),
                "total_orders":  d["total_orders"],
                "avg_order":     round(d["avg_order"], 2),
            }},
            upsert=True
        )
        for d in cat_data
    ]
    db[Collections.AGG_CATEGORIA].bulk_write(ops)
    print(f"  [+] agg_ventas_categoria: {len(ops)} categorías")

    # ── Ventas semanales ──────────────────────────────────────────
    pipe_sem = [
        {"$group": {
            "_id":          {"$substr": ["$order_date", 0, 7]},
            "total_revenue":{"$sum": "$total_amount"},
            "total_orders": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    sem_data = list(col.aggregate(pipe_sem))
    ops = [
        UpdateOne(
            {"week": d["_id"]},
            {"$set": {
                "week":          d["_id"],
                "total_revenue": round(d["total_revenue"], 2),
                "total_orders":  d["total_orders"],
            }},
            upsert=True
        )
        for d in sem_data
    ]
    db[Collections.AGG_SEMANAL].bulk_write(ops)
    print(f"  [+] agg_ventas_semanal: {len(ops)} meses")

    # ── Heatmap: país × categoría ─────────────────────────────────
    pipe_hm = [
        {"$group": {
            "_id":   {"country": "$country", "category": "$category"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}},
        {"$limit": 300},
    ]
    hm_data = list(col.aggregate(pipe_hm))
    ops = [
        UpdateOne(
            {"country": d["_id"]["country"], "category": d["_id"]["category"]},
            {"$set": {"country": d["_id"]["country"], "category": d["_id"]["category"], "count": d["count"]}},
            upsert=True
        )
        for d in hm_data
    ]
    db["agg_heatmap"].bulk_write(ops)
    print(f"  [+] agg_heatmap: {len(ops)} combinaciones")

    # ── Bubble: métricas por categoría ───────────────────────────
    pipe_bub = [
        {"$group": {
            "_id":               "$category",
            "avg_quantity":      {"$avg": "$quantity"},
            "avg_total_amount":  {"$avg": "$total_amount"},
            "avg_shipping_cost": {"$avg": "$shipping_cost"},
            "total":             {"$sum": "$total_amount"},
        }},
        {"$sort": {"total": -1}},
    ]
    bub_data = list(col.aggregate(pipe_bub))
    max_total = max((d["total"] for d in bub_data), default=1)
    ops = [
        UpdateOne(
            {"category": d["_id"]},
            {"$set": {
                "category":          d["_id"],
                "avg_quantity":      round(d["avg_quantity"], 2),
                "avg_total_amount":  round(d["avg_total_amount"], 2),
                "avg_shipping_cost": round(d["avg_shipping_cost"], 2),
                "bubble_size":       round(d["total"] / max_total * 60, 1),
            }},
            upsert=True
        )
        for d in bub_data
    ]
    db["agg_bubble"].bulk_write(ops)
    print(f"  [+] agg_bubble: {len(ops)} categorías")

    # ── Treemap: categoría × marca ────────────────────────────────
    pipe_tm = [
        {"$group": {
            "_id":          {"category": "$category", "brand": "$brand"},
            "total_amount": {"$sum": "$total_amount"},
        }},
        {"$sort": {"total_amount": -1}},
        {"$limit": 80},
    ]
    tm_data = list(col.aggregate(pipe_tm))
    ops = [
        UpdateOne(
            {"category": d["_id"]["category"], "brand": d["_id"]["brand"]},
            {"$set": {
                "category":     d["_id"]["category"],
                "brand":        d["_id"]["brand"],
                "total_amount": round(d["total_amount"], 2),
            }},
            upsert=True
        )
        for d in tm_data
    ]
    db["agg_treemap"].bulk_write(ops)
    print(f"  [+] agg_treemap: {len(ops)} combinaciones")

    # ── KPIs globales ─────────────────────────────────────────────
    kpi_pipe = [
        {"$group": {
            "_id":           None,
            "total_revenue": {"$sum": "$total_amount"},
            "avg_discount":  {"$avg": "$discount"},
            "total_orders":  {"$sum": 1},
        }}
    ]
    kpi = list(col.aggregate(kpi_pipe))
    if kpi:
        k = kpi[0]
        top_brand = list(col.aggregate([
            {"$group": {"_id": "$brand", "qty": {"$sum": "$quantity"}}},
            {"$sort": {"qty": -1}}, {"$limit": 1}
        ]))
        top_pay = list(col.aggregate([
            {"$group": {"_id": "$payment_method", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, {"$limit": 1}
        ]))
        db["agg_kpis"].update_one(
            {"_id": "global"},
            {"$set": {
                "total_revenue":     round(k["total_revenue"], 2),
                "avg_discount_pct":  round(k["avg_discount"] * 100, 1),
                "total_orders":      k["total_orders"],
                "top_brand":         top_brand[0]["_id"] if top_brand else "N/A",
                "top_payment":       top_pay[0]["_id"] if top_pay else "N/A",
            }},
            upsert=True
        )
        print(f"  [+] agg_kpis: global")

    print("[Agg] ✅ Agregaciones completadas.")


if __name__ == "__main__":
    build_aggregations()