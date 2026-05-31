"""
upload_to_pocketbase.py
───────────────────────
Lee el CSV de Amazon y sube todos los registros
a la colección 'amazon_sales' de PocketBase.
"""

import csv
import json
import requests
import time

# ── Configuración ──────────────────────────────────────────────────
POCKETBASE_URL = "http://localhost:8090"
PB_EMAIL       = "admin@swiftship.com"
PB_PASSWORD    = "admin1234"
COLLECTION     = "amazon_sales"
CSV_PATH       = r"C:\Users\ASUS\Desktop\BackUp\Amazon.csv"
BATCH_SIZE     = 50   # Registros por lote


# ── Autenticación ──────────────────────────────────────────────────
def authenticate():
    url  = f"{POCKETBASE_URL}/api/collections/_superusers/auth-with-password"
    resp = requests.post(url, json={"identity": PB_EMAIL, "password": PB_PASSWORD})
    resp.raise_for_status()
    token = resp.json()["token"]
    print(f"[OK] Autenticado en PocketBase.")
    return token


# ── Subir un registro ──────────────────────────────────────────────
def upload_record(token, record):
    url     = f"{POCKETBASE_URL}/api/collections/{COLLECTION}/records"
    headers = {"Authorization": f"Bearer {token}"}
    resp    = requests.post(url, headers=headers, json=record)
    return resp.status_code in (200, 201)


# ── Main ───────────────────────────────────────────────────────────
def main():
    token = authenticate()

    with open(CSV_PATH, encoding="utf-8") as f:
        reader  = list(csv.DictReader(f))
        total   = len(reader)
        success = 0
        errors  = 0

        print(f"[INFO] Total de registros a subir: {total:,}")
        print(f"[INFO] Esto puede tardar varios minutos, espera...\n")

        for i, row in enumerate(reader):
            # Convertir tipos numéricos
            record = {
                "OrderID":       row["OrderID"],
                "OrderDate":     row["OrderDate"],
                "CustomerID":    row["CustomerID"],
                "CustomerName":  row["CustomerName"],
                "ProductID":     row["ProductID"],
                "ProductName":   row["ProductName"],
                "Category":      row["Category"],
                "Brand":         row["Brand"],
                "Quantity":      int(row["Quantity"]),
                "UnitPrice":     float(row["UnitPrice"]),
                "Discount":      float(row["Discount"]),
                "Tax":           float(row["Tax"]),
                "ShippingCost":  float(row["ShippingCost"]),
                "TotalAmount":   float(row["TotalAmount"]),
                "PaymentMethod": row["PaymentMethod"],
                "OrderStatus":   row["OrderStatus"],
                "City":          row["City"],
                "State":         row["State"],
                "Country":       row["Country"],
                "SellerID":      row["SellerID"],
            }

            if upload_record(token, record):
                success += 1
            else:
                errors += 1

            # Progreso cada 500 registros
            if (i + 1) % 500 == 0:
                print(f"  → {i + 1:,} / {total:,} registros ({success:,} OK, {errors} errores)")

    print(f"\n[DONE] Subida completa.")
    print(f"  ✅ Exitosos: {success:,}")
    print(f"  ❌ Errores:  {errors}")


if __name__ == "__main__":
    main()