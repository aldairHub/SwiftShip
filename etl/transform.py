"""
etl/transform.py
────────────────
Limpia el dataset original, genera 100k registros
adicionales con Faker y guarda todo en Parquet en stage/.
"""

import os
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from faker import Faker

fake = Faker()
random.seed(42)

STAGE_DIR = Path("stage")
STAGE_DIR.mkdir(exist_ok=True)

VALID_STATUSES  = ["Pending", "Shipped", "Delivered", "Cancelled", "Returned"]
VALID_PAYMENTS  = ["Credit Card", "Debit Card", "PayPal", "Bank Transfer", "Cash on Delivery"]
VALID_COUNTRIES = ["USA", "India", "Germany", "UK", "France", "Brazil", "Canada", "Australia", "Mexico", "Spain"]
VALID_CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Beauty", "Automotive"]
VALID_BRANDS = ["Samsung", "Apple", "Nike", "Adidas", "Sony", "LG", "Dell", "HP", "Zara", "IKEA", "CoreTech"]


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y normaliza el DataFrame original."""

    # Renombrar columnas a snake_case
    df = df.rename(columns={
        "OrderID":       "order_id",
        "OrderDate":     "order_date",
        "CustomerID":    "customer_id",
        "CustomerName":  "customer_name",
        "ProductID":     "product_id",
        "ProductName":   "product_name",
        "Category":      "category",
        "Brand":         "brand",
        "Quantity":      "quantity",
        "UnitPrice":     "unit_price",
        "Discount":      "discount",
        "Tax":           "tax",
        "ShippingCost":  "shipping_cost",
        "TotalAmount":   "total_amount",
        "PaymentMethod": "payment_method",
        "OrderStatus":   "status",
        "City":          "city",
        "State":         "state",
        "Country":       "country",
        "SellerID":      "seller_id",
    })

    # Tipos correctos
    df["order_date"]   = pd.to_datetime(df["order_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["quantity"]     = pd.to_numeric(df["quantity"],     errors="coerce").fillna(0).astype(int)
    df["unit_price"]   = pd.to_numeric(df["unit_price"],   errors="coerce").fillna(0).round(2)
    df["discount"]     = pd.to_numeric(df["discount"],     errors="coerce").fillna(0).round(2)
    df["tax"]          = pd.to_numeric(df["tax"],          errors="coerce").fillna(0).round(2)
    df["shipping_cost"]= pd.to_numeric(df["shipping_cost"],errors="coerce").fillna(0).round(2)
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce").fillna(0).round(2)

    # Limpiar strings
    str_cols = ["order_id", "customer_name", "product_name", "category",
                "brand", "city", "state", "country", "status", "payment_method"]
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()

    # Eliminar filas sin order_id
    df = df[df["order_id"].str.strip() != ""]
    df = df.dropna(subset=["order_id"])

    return df


def _generate_extra(n: int, existing_ids: set) -> pd.DataFrame:
    """Genera n registros sintéticos con Faker."""
    print(f"[Transform] Generando {n:,} registros adicionales...")
    rows = []
    start = datetime(2020, 1, 1)
    end   = datetime(2024, 12, 31)
    days  = (end - start).days

    for i in range(n):
        oid = f"SS-{uuid.uuid4().hex[:8].upper()}"
        while oid in existing_ids:
            oid = f"SS-{uuid.uuid4().hex[:8].upper()}"
        existing_ids.add(oid)

        qty      = random.randint(1, 10)
        price    = round(random.uniform(5.0, 1500.0), 2)
        discount = round(random.uniform(0.0, 0.4), 2)
        tax      = round(price * qty * 0.12, 2)
        shipping = round(random.uniform(2.0, 50.0), 2)
        total    = round(price * qty * (1 - discount) + tax + shipping, 2)
        brand    = random.choice(VALID_BRANDS)
        category = random.choice(VALID_CATEGORIES)
        dt       = (start + timedelta(days=random.randint(0, days))).strftime("%Y-%m-%d")

        rows.append({
            "order_id":      oid,
            "order_date":    dt,
            "customer_id":   f"CUST{random.randint(10000, 99999)}",
            "customer_name": fake.name(),
            "product_id":    f"P{random.randint(1000, 9999)}",
            "product_name":  f"{brand} {category} {random.randint(100, 999)}",
            "category":      category,
            "brand":         brand,
            "quantity":      qty,
            "unit_price":    price,
            "discount":      discount,
            "tax":           tax,
            "shipping_cost": shipping,
            "total_amount":  total,
            "payment_method": random.choice(VALID_PAYMENTS),
            "status":        random.choice(VALID_STATUSES),
            "city":          fake.city(),
            "state":         fake.state(),
            "country":       random.choice(VALID_COUNTRIES),
            "seller_id":     f"SELL{random.randint(100, 999):05d}",
        })

        if (i + 1) % 10000 == 0:
            print(f"  → {i + 1:,} generados...")

    return pd.DataFrame(rows)


def transform(df_raw: pd.DataFrame) -> Path:
    """
    Limpia el dataset, genera registros adicionales
    y guarda en Parquet en stage/.
    """
    print(f"[Transform] Registros entrada: {len(df_raw):,}")

    df_clean = _clean(df_raw.copy())
    print(f"[Transform] Después de limpieza: {len(df_clean):,}")

    existing_ids = set(df_clean["order_id"].tolist())
    extra_needed = max(0, 300_000 - len(df_clean))

    if extra_needed > 0:
        df_extra = _generate_extra(extra_needed, existing_ids)
        df_final = pd.concat([df_clean, df_extra], ignore_index=True)
    else:
        df_final = df_clean

    print(f"[Transform] Total final: {len(df_final):,} registros.")

    # Guardar Parquet
    path = STAGE_DIR / "swiftship_latest.parquet"
    table = pa.Table.from_pandas(df_final, preserve_index=False)
    pq.write_table(table, path, compression="snappy")
    size = path.stat().st_size / 1024 / 1024
    print(f"[Transform] Parquet guardado en: {path} ({size:.1f} MB)")

    return path