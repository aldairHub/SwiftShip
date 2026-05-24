"""
etl/load.py
───────────
Lee el Parquet de stage/ y carga todas las
colecciones en MongoDB (dimensiones + hechos).
"""

from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
from tqdm import tqdm
from pymongo import UpdateOne
from faker import Faker
import random

from db.mongo_connector import get_db, Collections, create_indexes

fake = Faker()
random.seed(99)

BATCH_SIZE = 1000


def _bulk_upsert(collection, docs: list, key: str):
    """Inserta o actualiza documentos en lote."""
    ops = [
        UpdateOne({key: d[key]}, {"$set": d}, upsert=True)
        for d in docs
    ]
    for i in range(0, len(ops), BATCH_SIZE):
        collection.bulk_write(ops[i:i + BATCH_SIZE], ordered=False)


# ── Dimensiones ────────────────────────────────────────────────────

def _load_categorias(db, df):
    docs = [{"name": c} for c in sorted(df["category"].unique())]
    _bulk_upsert(db[Collections.CATEGORIAS], docs, "name")
    print(f"  [+] Categorías:     {len(docs)}")


def _load_marcas(db, df):
    docs = [{"name": b} for b in sorted(df["brand"].unique())]
    _bulk_upsert(db[Collections.MARCAS], docs, "name")
    print(f"  [+] Marcas:         {len(docs)}")


def _load_metodos_pago(db, df):
    docs = [{"name": m} for m in sorted(df["payment_method"].unique())]
    _bulk_upsert(db[Collections.METODOS_PAGO], docs, "name")
    print(f"  [+] Métodos pago:   {len(docs)}")


def _load_estados(db, df):
    docs = [{"name": s} for s in sorted(df["status"].unique())]
    _bulk_upsert(db[Collections.ESTADOS], docs, "name")
    print(f"  [+] Estados:        {len(docs)}")


def _load_ubicaciones(db, df):
    locs = df[["city", "state", "country"]].drop_duplicates().reset_index(drop=True)
    docs = locs.to_dict(orient="records")
    for i, d in enumerate(docs):
        d["location_id"] = i + 1
    _bulk_upsert(db[Collections.UBICACIONES], docs, "location_id")
    print(f"  [+] Ubicaciones:    {len(docs)}")


def _load_clientes(db, df):
    cli = df[["customer_id", "customer_name", "city", "state", "country"]].drop_duplicates("customer_id")
    docs = cli.rename(columns={"customer_name": "name"}).to_dict(orient="records")
    _bulk_upsert(db[Collections.CLIENTES], docs, "customer_id")
    print(f"  [+] Clientes:       {len(docs)}")


def _load_productos(db, df):
    prod = df[["product_id", "product_name", "category", "brand", "unit_price"]].drop_duplicates("product_id")
    docs = prod.rename(columns={"product_name": "name"}).to_dict(orient="records")
    _bulk_upsert(db[Collections.PRODUCTOS], docs, "product_id")
    print(f"  [+] Productos:      {len(docs)}")


def _load_vendedores(db, df):
    seller_ids = df["seller_id"].unique()
    existing   = {d["seller_id"] for d in db[Collections.VENDEDORES].find({}, {"seller_id": 1})}
    nuevos = []
    for sid in seller_ids:
        if sid not in existing:
            nuevos.append({
                "seller_id":   sid,
                "name":        fake.name(),
                "email":       fake.email(),
                "phone":       fake.phone_number(),
                "city":        fake.city(),
                "country":     fake.country(),
                "rating":      round(random.uniform(3.0, 5.0), 1),
                "active":      random.choice([True, True, True, False]),
                "joined_date": fake.date_between(start_date="-5y", end_date="today").isoformat(),
            })
    if nuevos:
        _bulk_upsert(db[Collections.VENDEDORES], nuevos, "seller_id")
    print(f"  [+] Vendedores:     {len(seller_ids)} únicos | {len(nuevos)} nuevos")


# ── Hechos ─────────────────────────────────────────────────────────

def _load_pedidos(db, df):
    print(f"  [+] Cargando {len(df):,} pedidos...")
    docs = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="  Pedidos", unit="reg"):
        docs.append({
            "order_id":       str(row["order_id"]),
            "order_date":     str(row["order_date"]),
            "customer_id":    str(row["customer_id"]),
            "customer_name":  str(row["customer_name"]),
            "product_id":     str(row["product_id"]),
            "product_name":   str(row["product_name"]),
            "category":       str(row["category"]),
            "brand":          str(row["brand"]),
            "seller_id":      str(row["seller_id"]),
            "payment_method": str(row["payment_method"]),
            "status":         str(row["status"]),
            "city":           str(row["city"]),
            "state":          str(row["state"]),
            "country":        str(row["country"]),
            "quantity":       int(row["quantity"]),
            "unit_price":     float(row["unit_price"]),
            "discount":       float(row["discount"]),
            "tax":            float(row["tax"]),
            "shipping_cost":  float(row["shipping_cost"]),
            "total_amount":   float(row["total_amount"]),
        })

        if len(docs) >= BATCH_SIZE:
            _bulk_upsert(db[Collections.PEDIDOS], docs, "order_id")
            docs = []

    if docs:
        _bulk_upsert(db[Collections.PEDIDOS], docs, "order_id")


# ── Principal ──────────────────────────────────────────────────────

def load(parquet_path: Path):
    print(f"\n[Load] Leyendo: {parquet_path}")
    df = pq.read_table(parquet_path).to_pandas()
    print(f"[Load] {len(df):,} registros leídos.\n")

    db = get_db()
    create_indexes()

    print("[Load] Cargando dimensiones...")
    _load_categorias(db, df)
    _load_marcas(db, df)
    _load_metodos_pago(db, df)
    _load_estados(db, df)
    _load_ubicaciones(db, df)
    _load_clientes(db, df)
    _load_productos(db, df)
    _load_vendedores(db, df)

    print("\n[Load] Cargando hechos...")
    _load_pedidos(db, df)

    print("\n[Load] ✅ Carga completa en MongoDB.")