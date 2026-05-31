"""
test_load.py
────────────
Prueba el paso Load del ETL.
Lee el Parquet existente en stage/ y carga a MongoDB.
"""

import sys
sys.path.insert(0, ".")

from pathlib import Path
from etl.load import load

parquet_path = Path("stage/swiftship_latest.parquet")

if not parquet_path.exists():
    print("❌ No se encontró el Parquet. Ejecuta primero test_transform.py")
    sys.exit(1)

load(parquet_path)