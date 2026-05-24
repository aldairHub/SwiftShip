"""
SwiftShip - Generador de estructura completa
Corre este script desde C:\\Users\\ASUS\\Desktop\\SwiftShip
Comando: .venv\\Scripts\\python.exe crear_estructura.py
"""

import os

BASE = os.path.dirname(os.path.abspath(__file__))

def crear(path, contenido=""):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(contenido)
        print(f"  ✅ creado: {os.path.relpath(path, BASE)}")
    else:
        print(f"  ⏭  existe: {os.path.relpath(path, BASE)}")

def mkdir(path):
    os.makedirs(path, exist_ok=True)

# ─────────────────────────────────────────────
# PAQUETES / __init__.py raíz
# ─────────────────────────────────────────────
crear(f"{BASE}/paquetes/__init__.py", "# Paquetes de SwiftShip\n")

# ─────────────────────────────────────────────
# PAQUETE 1 — Acceso y Seguridad (SEMANA 1 ✅)
# ─────────────────────────────────────────────
P1 = f"{BASE}/paquetes/p1_acceso_seguridad"

crear(f"{P1}/__init__.py", "# Paquete 1: Gestión de Acceso y Seguridad\n")

crear(f"{P1}/cu01_registro/__init__.py", "# CU-01: Registrar Vendedor\n")
crear(f"{P1}/cu01_registro/routes.py",
"""# CU-01: Registrar Vendedor
# Rutas: GET /auth/registro  |  POST /auth/registro
from flask import Blueprint

cu01_registro_bp = Blueprint('cu01_registro', __name__)

# TODO: implementar
""")

crear(f"{P1}/cu02_login/__init__.py", "# CU-02: Autenticar Usuario\n")
crear(f"{P1}/cu02_login/routes.py",
"""# CU-02: Autenticar Usuario (Login)
# Rutas: GET /auth/login  |  POST /auth/login
from flask import Blueprint

cu02_login_bp = Blueprint('cu02_login', __name__)

# TODO: implementar
""")

crear(f"{P1}/cu03_control_acceso/__init__.py", "# CU-03: Controlar Acceso por Rol\n")
crear(f"{P1}/cu03_control_acceso/decorators.py",
"""# CU-03: Controlar Acceso por Rol
# Decoradores: @requiere_login  @requiere_admin  @requiere_vendedor

# TODO: implementar
""")

crear(f"{P1}/cu04_logout/__init__.py", "# CU-04: Cerrar Sesión\n")
crear(f"{P1}/cu04_logout/routes.py",
"""# CU-04: Cerrar Sesión
# Ruta: GET /auth/logout
from flask import Blueprint

cu04_logout_bp = Blueprint('cu04_logout', __name__)

# TODO: implementar
""")

# ─────────────────────────────────────────────
# PAQUETE 2 — Portal del Vendedor (SEMANA 2 🔒)
# ─────────────────────────────────────────────
P2 = f"{BASE}/paquetes/p2_portal_vendedor"

crear(f"{P2}/__init__.py", "# Paquete 2: Portal del Vendedor — Semana 2\n")

for cu, nombre in [
    ("cu05_crear_envio",    "CU-05: Crear Nuevo Envío"),
    ("cu06_mis_pedidos",    "CU-06: Consultar Mis Pedidos"),
    ("cu07_cancelar_pedido","CU-07: Cancelar Pedido"),
    ("cu08_mis_metricas",   "CU-08: Ver Mis Métricas de Rendimiento"),
]:
    crear(f"{P2}/{cu}/__init__.py", f"# {nombre} — Pendiente Semana 2\n")
    crear(f"{P2}/{cu}/routes.py",
f"""# {nombre}
# Pendiente: Semana 2 — Portal del Vendedor
from flask import Blueprint

{cu}_bp = Blueprint('{cu}', __name__)
""")

# ─────────────────────────────────────────────
# PAQUETE 3 — Operación Logística (SEMANA 3 🔒)
# ─────────────────────────────────────────────
P3 = f"{BASE}/paquetes/p3_operacion_logistica"

crear(f"{P3}/__init__.py", "# Paquete 3: Operación Logística — Semana 3\n")

for cu, nombre in [
    ("cu09_actualizar_estado",  "CU-09: Actualizar Estado de Pedido"),
    ("cu10_alertas",            "CU-10: Detectar Pedidos Sin Movimiento"),
    ("cu11_rastreo_publico",    "CU-11: Rastrear Pedido (Público)"),
    ("cu12_historial_estados",  "CU-12: Ver Historial de Estados"),
]:
    crear(f"{P3}/{cu}/__init__.py", f"# {nombre} — Pendiente Semana 3\n")
    crear(f"{P3}/{cu}/routes.py",
f"""# {nombre}
# Pendiente: Semana 3 — Operación Logística
from flask import Blueprint

{cu}_bp = Blueprint('{cu}', __name__)
""")

# ─────────────────────────────────────────────
# PAQUETE 4 — Inteligencia y Escala (SEMANA 4 🔒)
# ─────────────────────────────────────────────
P4 = f"{BASE}/paquetes/p4_inteligencia_escala"

crear(f"{P4}/__init__.py", "# Paquete 4: Inteligencia y Escala — Semana 4\n")

for cu, nombre in [
    ("cu13_dashboard",  "CU-13: Visualizar Dashboard Analítico"),
    ("cu14_filtros",    "CU-14: Filtrar y Analizar Pedidos"),
    ("cu15_exportar",   "CU-15: Exportar Datos a CSV"),
    ("cu16_admin",      "CU-16: Administrar Sistema"),
]:
    crear(f"{P4}/{cu}/__init__.py", f"# {nombre} — Pendiente Semana 4\n")
    crear(f"{P4}/{cu}/routes.py",
f"""# {nombre}
# Pendiente: Semana 4 — Inteligencia y Escala
from flask import Blueprint

{cu}_bp = Blueprint('{cu}', __name__)
""")

# ─────────────────────────────────────────────
# TEMPLATES nuevos
# ─────────────────────────────────────────────
for carpeta in ["p1_acceso", "p2_vendedor", "p3_operacion", "p4_inteligencia"]:
    mkdir(f"{BASE}/templates/{carpeta}")

crear(f"{BASE}/templates/p1_acceso/login.html",    "<!-- CU-02: Login — pendiente implementación -->\n")
crear(f"{BASE}/templates/p1_acceso/registro.html", "<!-- CU-01: Registro Vendedor — pendiente implementación -->\n")

# ─────────────────────────────────────────────
# CSS nuevos
# ─────────────────────────────────────────────
crear(f"{BASE}/static/css/auth.css", "/* Estilos de autenticación — CU-01, CU-02 */\n")

print("\n✅ Estructura SwiftShip generada correctamente.")
print("   Semanas 2, 3 y 4 tienen placeholders listos.")
print("   Semana 1 (p1_acceso_seguridad) lista para implementar.\n")