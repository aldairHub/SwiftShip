"""
config.py — Environment variable loading and validation.

Reads all required configuration from environment variables at import time.
If any required variable is missing, logs an error and exits with code 1.
All constants are exposed at module level for import by other modules.

Validates: Requirements 1.1, 9.1, 9.2
"""

import logging
import os
import sys

logger = logging.getLogger(__name__)

_REQUIRED_VARS = [
    "DB_HOST",
    "DB_PORT",
    "DB_USER",
    "DB_PASSWORD",
    "FLASK_SECRET_KEY",
]


def _load_config() -> dict:
    """
    Read each required environment variable. Log an error and call
    sys.exit(1) for the first missing variable found.
    Returns a dict of all resolved values.
    """
    values: dict = {}
    for var in _REQUIRED_VARS:
        value = os.environ.get(var)
        if value is None:
            logger.error("Missing required environment variable: %s", var)
            sys.exit(1)
        values[var] = value
    return values


_config = _load_config()

# ---------------------------------------------------------------------------
# Module-level constants — import these in other modules
# ---------------------------------------------------------------------------

DB_HOST: str = _config["DB_HOST"]
DB_PORT: str = _config["DB_PORT"]
DB_USER: str = _config["DB_USER"]
DB_PASSWORD: str = _config["DB_PASSWORD"]
FLASK_SECRET_KEY: str = _config["FLASK_SECRET_KEY"]
