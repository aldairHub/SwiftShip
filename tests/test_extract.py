"""
test_extract.py
───────────────
Prueba que el extract de PocketBase funciona.
"""

import sys
sys.path.insert(0, ".")

from etl.extract import extract_from_pocketbase

df = extract_from_pocketbase()

print(f"\nColumnas: {list(df.columns)}")
print(f"Registros: {len(df):,}")
print(f"\nPrimera fila:")
print(df.iloc[0].to_dict())