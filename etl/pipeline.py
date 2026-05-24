"""
etl/pipeline.py
───────────────
Orquestador completo del ETL de SwiftShip.
Uso: .venv\\Scripts\\python.exe -m etl.pipeline
"""

import sys
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

import time
from etl.extract      import extract_from_pocketbase
from etl.transform    import transform
from etl.load         import load
from etl.pipeline_agg import build_aggregations


def run():
    print("=" * 50)
    print("  SwiftShip ETL Pipeline")
    print("=" * 50)
    t0 = time.time()

    print("\n[1/4] EXTRACT")
    df_raw = extract_from_pocketbase()

    print("\n[2/4] TRANSFORM")
    parquet_path = transform(df_raw)

    print("\n[3/4] LOAD")
    load(parquet_path)

    print("\n[4/4] AGGREGATIONS")
    build_aggregations()

    print(f"\n{'='*50}")
    print(f"  ✅ Pipeline completo en {time.time() - t0:.1f}s")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    run()