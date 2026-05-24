"""
etl/extract.py
──────────────
Descarga todos los registros de PocketBase
y los retorna como un DataFrame de pandas.
"""

import requests
import pandas as pd
from tqdm import tqdm

POCKETBASE_URL = "http://localhost:8090"
PB_EMAIL       = "admin@swiftship.com"
PB_PASSWORD    = "admin1234"
COLLECTION     = "amazon_sales"
PAGE_SIZE      = 200


def _authenticate() -> str:
    url  = f"{POCKETBASE_URL}/api/collections/_superusers/auth-with-password"
    resp = requests.post(url, json={"identity": PB_EMAIL, "password": PB_PASSWORD}, timeout=10)
    resp.raise_for_status()
    print("[Extract] Autenticado en PocketBase.")
    return resp.json()["token"]


def _fetch_page(token: str, page: int) -> dict:
    url     = f"{POCKETBASE_URL}/api/collections/{COLLECTION}/records"
    headers = {"Authorization": f"Bearer {token}"}
    params  = {"page": page, "perPage": PAGE_SIZE, "sort": "+id"}
    resp    = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def extract_from_pocketbase() -> pd.DataFrame:
    token      = _authenticate()
    first      = _fetch_page(token, 1)
    total      = first["totalItems"]
    pages      = first["totalPages"]
    records    = first["items"]

    print(f"[Extract] {total:,} registros encontrados en PocketBase.")

    with tqdm(total=pages, desc="[Extract] Descargando", unit="pág") as pbar:
        pbar.update(1)
        for page in range(2, pages + 1):
            records.extend(_fetch_page(token, page)["items"])
            pbar.update(1)

    df = pd.DataFrame(records)

    # Eliminar columnas internas de PocketBase
    cols_borrar = ["id", "collectionId", "collectionName", "created", "updated"]
    df.drop(columns=[c for c in cols_borrar if c in df.columns], inplace=True)

    print(f"[Extract] Extracción completa: {len(df):,} registros, {len(df.columns)} columnas.")
    return df