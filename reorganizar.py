"""
reorganizar.py — Limpia la estructura del repo SwiftShip
Corre desde la raíz: .venv\Scripts\python.exe reorganizar.py
"""
import os, shutil
from pathlib import Path

BASE = Path(__file__).parent

def mover(origen, destino):
    o = BASE / origen
    d = BASE / destino
    if o.exists():
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(o), str(d))
        print(f"  ✅ {origen} → {destino}")
    else:
        print(f"  ⏭  no existe: {origen}")

print("\n── Moviendo scripts de utilidad a scripts/ ──")
mover("seed_admin.py",          "scripts/seed_admin.py")
mover("crear_estructura.py",    "scripts/crear_estructura.py")
mover("fix.py",                 "scripts/fix.py")
mover("upload_to_pocketbase.py","scripts/upload_to_pocketbase.py")
mover("app_postgres_backup.py", "scripts/app_postgres_backup.py")

print("\n── Moviendo tests a tests/ ──")
mover("test_extract.py",  "tests/test_extract.py")
mover("test_load.py",     "tests/test_load.py")
mover("test_mongo.py",    "tests/test_mongo.py")
mover("test_transform.py","tests/test_transform.py")

print("\n── Limpiando carpetas vacías ──")
for carpeta in ["charts", "filters"]:
    p = BASE / carpeta
    if p.exists() and not any(p.iterdir()):
        p.rmdir()
        print(f"  🗑️  eliminada carpeta vacía: {carpeta}/")
    elif p.exists():
        print(f"  ⚠️  {carpeta}/ tiene archivos, no se eliminó")

print("\n✅ Reorganización completa.\n")