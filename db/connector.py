"""
db/connector.py — Connection pool management for SwiftShip Logistics Dashboard.

Manages the lifecycle of a psycopg2 ThreadedConnectionPool and executes
parameterized queries safely.

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
"""

import logging
import time

import psycopg2
import psycopg2.extensions
import psycopg2.extras
import psycopg2.pool
from psycopg2 import extensions as _ext
from psycopg2 import OperationalError as PsycopgOperationalError
from psycopg2.extensions import QueryCanceledError

import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------

_IDLE_TIMEOUT_SECONDS = 300  # reconnect if connection idle > 300 s


class SwiftShipError(Exception):
    """Base exception for all SwiftShip application errors."""


class FilterValidationError(SwiftShipError):
    """Raised when filter parameters fail validation (→ HTTP 400)."""


class QueryTimeoutError(SwiftShipError):
    """Raised when a query exceeds the 30-second statement timeout (→ HTTP 504)."""


class PoolExhaustedError(SwiftShipError):
    """Raised when no connection is available from the pool within 5 s (→ HTTP 503)."""


class ConnectionError(SwiftShipError):
    """Raised when a database connection cannot be established or re-established."""


class DBConnector:
    """Manages a psycopg2 ThreadedConnectionPool and executes parameterized queries."""

    def __init__(self) -> None:
        """
        Initialize the connection pool reading DB_HOST, DB_PORT, DB_USER,
        DB_PASSWORD from config.py (which already validated them at import time).

        Pool: minconn=2, maxconn=10.
        connection_timeout=5 seconds (used in execute_query when waiting for a
        free connection from the pool).

        Raises SystemExit(1) if the pool cannot be initialized.
        """
        self.connection_timeout: int = 5
        self._last_used: dict = {}  # maps connection id → last-used timestamp

        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                dbname="amazon",
            )
            logger.info(
                "Connection pool initialized (host=%s, port=%s, minconn=2, maxconn=10).",
                config.DB_HOST,
                config.DB_PORT,
            )
        except psycopg2.Error as exc:
            logger.error(
                "Failed to initialize connection pool: %s (host=%s, port=%s)",
                type(exc).__name__,
                config.DB_HOST,
                config.DB_PORT,
            )
            raise SystemExit(1) from exc

    def execute_query(self, sql: str, params: tuple = ()) -> list[dict]:
        """
        Obtain a connection from the pool (waiting up to ``connection_timeout``
        seconds), execute a parameterized query, and return the results as a
        list of dicts.

        Steps:
        1. Wait up to 5 s for a free connection; raise PoolExhaustedError if none.
        2. If the connection has been idle >300 s, verify it with SELECT 1 and
           reconnect if the check fails.
        3. If conn.closed != 0, get a fresh connection from the pool.
        4. Set ``statement_timeout`` to 30 000 ms for this session.
        5. Execute the parameterized SQL.
        6. Map rows to dicts using cursor.description column names.
        7. Always return the connection to the pool in a finally block.

        Raises:
            PoolExhaustedError: No connection available within 5 s.
            QueryTimeoutError:  Query exceeded 30-second statement timeout.
            ConnectionError:    Connection could not be re-established.

        Never exposes DB_PASSWORD in any error message or log.

        Validates: Requirements 1.3, 1.4, 1.5, 1.6, 1.7
        """
        conn = None
        deadline = time.time() + self.connection_timeout

        # ------------------------------------------------------------------
        # 1. Acquire a connection from the pool within the timeout window.
        # ------------------------------------------------------------------
        while True:
            try:
                conn = self._pool.getconn()
                break
            except psycopg2.pool.PoolError:
                if time.time() >= deadline:
                    raise PoolExhaustedError("Connection pool exhausted")
                time.sleep(0.1)

        try:
            conn_key = id(conn)

            # ------------------------------------------------------------------
            # 2 & 3. Validate / reconnect stale or closed connections.
            # ------------------------------------------------------------------
            now = time.time()
            idle_seconds = now - self._last_used.get(conn_key, 0)
            needs_check = conn.closed != 0 or idle_seconds > _IDLE_TIMEOUT_SECONDS

            if needs_check:
                if conn.closed != 0:
                    # Connection is closed — get a brand-new one.
                    try:
                        self._pool.putconn(conn, close=True)
                    except Exception:
                        pass
                    try:
                        conn = self._pool.getconn()
                        conn_key = id(conn)
                    except psycopg2.pool.PoolError as exc:
                        raise PoolExhaustedError("Connection pool exhausted") from exc
                else:
                    # Connection has been idle too long — probe with SELECT 1.
                    try:
                        with conn.cursor() as probe:
                            probe.execute("SELECT 1")
                        conn.rollback()  # reset any implicit transaction state
                    except psycopg2.Error as exc:
                        logger.warning(
                            "Idle connection probe failed (%s, host=%s:%s); reconnecting.",
                            type(exc).__name__,
                            config.DB_HOST,
                            config.DB_PORT,
                        )
                        try:
                            self._pool.putconn(conn, close=True)
                        except Exception:
                            pass
                        try:
                            conn = self._pool.getconn()
                            conn_key = id(conn)
                        except psycopg2.pool.PoolError as pool_exc:
                            raise PoolExhaustedError("Connection pool exhausted") from pool_exc

            # ------------------------------------------------------------------
            # 4–6. Execute the query with a per-session statement timeout.
            # ------------------------------------------------------------------
            try:
                with conn.cursor() as cursor:
                    # Set a 30-second statement timeout for this session.
                    cursor.execute("SET LOCAL statement_timeout = '30000'")
                    # Execute the caller's parameterized SQL.
                    cursor.execute(sql, params)
                    columns = [col.name for col in cursor.description]
                    rows = cursor.fetchall()
                conn.commit()
            except QueryCanceledError as exc:
                conn.rollback()
                raise QueryTimeoutError("Query timeout after 30 seconds") from exc
            except PsycopgOperationalError as exc:
                conn.rollback()
                if "canceling statement due to statement timeout" in str(exc):
                    raise QueryTimeoutError("Query timeout after 30 seconds") from exc
                logger.error(
                    "Operational error executing query: %s (host=%s:%s)",
                    type(exc).__name__,
                    config.DB_HOST,
                    config.DB_PORT,
                )
                raise
            except psycopg2.Error as exc:
                conn.rollback()
                logger.error(
                    "Database error executing query: %s (host=%s:%s)",
                    type(exc).__name__,
                    config.DB_HOST,
                    config.DB_PORT,
                )
                raise

            # Record the last-used timestamp for idle-connection tracking.
            self._last_used[conn_key] = time.time()

            return [dict(zip(columns, row)) for row in rows]

        finally:
            # ------------------------------------------------------------------
            # 7. Always return the connection to the pool.
            # ------------------------------------------------------------------
            if conn is not None:
                self._pool.putconn(conn)

    def close(self) -> None:
        """Close all connections in the pool cleanly."""
        self._pool.closeall()
        logger.info("Connection pool closed.")
