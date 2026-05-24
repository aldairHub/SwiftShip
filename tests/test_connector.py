"""
tests/test_connector.py — Unit tests for DBConnector.

Validates: Requirements 1.2
"""

import importlib
import logging
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DB_ENV = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_USER": "user",
    "DB_PASSWORD": "password",
    "FLASK_SECRET_KEY": "test-secret-key",
}


def _fresh_connector():
    """
    Return a DBConnector with a mocked pool.

    config.py calls sys.exit(1) at module-level when env vars are absent, so
    we must set them in os.environ *before* importing config or db.connector,
    then reload both modules to pick up the patched values.
    """
    # Inject env vars
    for k, v in _DB_ENV.items():
        os.environ.setdefault(k, v)

    # Force a clean reload so config re-reads the env vars we just set
    for mod in ("config", "db.connector"):
        if mod in sys.modules:
            del sys.modules[mod]

    with patch("psycopg2.pool.ThreadedConnectionPool") as _mock_pool_cls:
        from db.connector import DBConnector  # noqa: PLC0415
        connector = DBConnector()

    # Swap the real pool for a controllable mock
    connector._pool = MagicMock()
    return connector


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDBConnectorClose:
    """Tests for DBConnector.close() — Requirement 1.2."""

    def test_close_calls_pool_closeall(self):
        """close() must call pool.closeall() exactly once."""
        connector = _fresh_connector()
        connector.close()
        connector._pool.closeall.assert_called_once()

    def test_close_logs_message(self, caplog):
        """close() must log an info message after closing the pool."""
        connector = _fresh_connector()
        with caplog.at_level(logging.INFO, logger="db.connector"):
            connector.close()
        assert any("Connection pool closed" in record.message for record in caplog.records)
