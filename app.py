"""
app.py — Flask application factory for SwiftShip Logistics Dashboard.
Migrado de PostgreSQL a MongoDB.
"""

from dotenv import load_dotenv
load_dotenv()

import logging
import os

from flask import Flask, render_template
from flask_cors import CORS

from db.mongo_connector import get_db, create_indexes

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "swiftship_secret_key_2024")

    # ── Modo desarrollo/producción ────────────────────────────────────
    flask_env = os.environ.get("FLASK_ENV", "development")
    if flask_env == "production":
        app.debug = False
        logger.info("Running in production mode.")
    else:
        app.debug = True
        logger.info("Running in development mode.")

    # ── CORS ──────────────────────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Conexión MongoDB ──────────────────────────────────────────────
    with app.app_context():
        try:
            get_db()
            create_indexes()
            logger.info("MongoDB conectado correctamente.")
        except Exception as e:
            logger.error(f"Error conectando a MongoDB: {e}")

    # ── Blueprints (se irán agregando uno a uno) ──────────────────────
    from paquetes.p1_acceso_seguridad.cu01_registro.routes import registro_bp
    from paquetes.p1_acceso_seguridad.cu02_login.routes    import login_bp
    from paquetes.p1_acceso_seguridad.cu04_logout.routes   import logout_bp
    from api.orders  import orders_bp
    from api.charts  import charts_bp
    from api.sellers import sellers_bp
    from api.crud    import crud_bp

    app.register_blueprint(registro_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(logout_bp)
    app.register_blueprint(orders_bp,  url_prefix="/api/orders")
    app.register_blueprint(charts_bp,  url_prefix="/api/orders")
    app.register_blueprint(sellers_bp, url_prefix="/api/sellers")
    app.register_blueprint(crud_bp,    url_prefix="/api/crud")

    # ── Rutas HTML ────────────────────────────────────────────────────
    from paquetes.p1_acceso_seguridad.cu03_control_acceso.decorators import requiere_login, requiere_admin

    @app.route("/")
    @requiere_login
    def home():
        return render_template("home.html")

    @app.route("/dashboard")
    @requiere_login
    def index():
        return render_template("index.html")

    @app.route("/tracking")
    @requiere_login
    def tracking():
        return render_template("tracking.html")

    @app.route("/sellers")
    @requiere_login
    def sellers():
        return render_template("sellers.html")

    @app.route("/crud")
    @requiere_admin
    def crud():
        return render_template("crud.html")

    logger.info("SwiftShip app lista.")
    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000)