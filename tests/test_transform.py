"""
test_transform.py
─────────────────
Prueba el paso Transform del ETL.
"""

import sys
sys.path.insert(0, ".")

from etl.extract   import extract_from_pocketbase
from etl.transform import transform

print("=== EXTRACT ===")
df_raw = extract_from_pocketbase()

print("\n=== TRANSFORM ===")
parquet_path = transform(df_raw)

# Verificar el Parquet generado
import pyarrow.parquet as pq
tabla = pq.read_table(parquet_path)
df    = tabla.to_pandas()

print(f"\nVerificación del Parquet:")
print(f"  Registros: {len(df):,}")
print(f"  Columnas:  {list(df.columns)}")
print(f"  Muestra:")
print(df.head(3).to_string())