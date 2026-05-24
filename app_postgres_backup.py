"""
app.py — Flask application factory for SwiftShip Logistics Dashboard.

Registers all blueprints, configures CORS, and sets production/debug mode.

Validates: Requirements 8.1, 8.2, 9.4
"""


from dotenv import load_dotenv
load_dotenv()

import logging
import os

from flask import Flask, render_template
from flask_cors import CORS

import config
from db.connector import DBConnector
from filters.engine import FilterEngine
from charts.renderer import ChartRenderer
from api.orders import create_orders_blueprint
from api.charts import create_charts_blueprint
from api.sellers import create_sellers_blueprint

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
    app.secret_key = config.FLASK_SECRET_KEY

    # ── Production mode ───────────────────────────────────────────────
    flask_env = os.environ.get("FLASK_ENV", "development")
    if flask_env == "production":
        app.debug = False
        app.config["PROPAGATE_EXCEPTIONS"] = False
        logger.info("Running in production mode.")
    else:
        app.debug = True
        logger.info("Running in development mode.")

    # ── CORS ──────────────────────────────────────────────────────────
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Dependencies ──────────────────────────────────────────────────
    db = DBConnector()
    filter_engine = FilterEngine()
    chart_renderer = ChartRenderer(db)

    # ── Blueprints ────────────────────────────────────────────────────
    app.register_blueprint(create_orders_blueprint(db, filter_engine))
    app.register_blueprint(create_charts_blueprint(db, filter_engine, chart_renderer))
    app.register_blueprint(create_sellers_blueprint(db))

    # ── Frontend route ────────────────────────────────────────────────
    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/dashboard")
    def index():
        return render_template("index.html")

    @app.route("/tracking")
    def tracking():
        return render_template("tracking.html")

    @app.route("/sellers")
    def sellers():
        return render_template("sellers.html")

    logger.info("SwiftShip app created and ready.")
    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000)