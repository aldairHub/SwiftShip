"""
tests/test_charts.py — Unit tests for ChartRenderer.

Validates: Requirements 5.1, 6.1, 6.2, 6.3, 6.4
"""

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Bootstrap: inject required env vars before importing modules that call
# config.py at module level (config.py calls sys.exit(1) if vars are absent).
# ---------------------------------------------------------------------------
_DB_ENV = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_USER": "user",
    "DB_PASSWORD": "password",
    "FLASK_SECRET_KEY": "test-secret-key",
}
for _k, _v in _DB_ENV.items():
    os.environ.setdefault(_k, _v)

from charts.renderer import ChartRenderer  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NO_FILTER = 'ORDER BY "OrderDate" DESC LIMIT 1000'
WITH_FILTER = 'WHERE "Country" IN %s ORDER BY "OrderDate" DESC LIMIT 1000'
PARAMS = (("Germany",),)


def _renderer(rows=None):
    """Return a ChartRenderer whose _db.execute_query returns `rows`."""
    db = MagicMock()
    db.execute_query.return_value = rows if rows is not None else []
    return ChartRenderer(db)


# ---------------------------------------------------------------------------
# 1. _bar_total_amount_by_country
# ---------------------------------------------------------------------------

class TestBarTotalAmountByCountry:
    """Tests for _bar_total_amount_by_country — Requirement 5.1."""

    def test_returns_labels_and_values(self):
        rows = [
            {"Country": "Germany", "total_amount": 1500.50},
            {"Country": "France", "total_amount": 1200.00},
        ]
        renderer = _renderer(rows)
        result = renderer._bar_total_amount_by_country(NO_FILTER, ())
        assert result["labels"] == ["Germany", "France"]
        assert result["values"] == [1500.50, 1200.00]

    def test_empty_rows_returns_empty_structure(self):
        renderer = _renderer([])
        result = renderer._bar_total_amount_by_country(NO_FILTER, ())
        assert result == {"labels": [], "values": []}

    def test_strips_order_by_suffix_from_where(self):
        """The SQL sent to execute_query must not contain the ORDER BY suffix."""
        renderer = _renderer([])
        renderer._bar_total_amount_by_country(WITH_FILTER, PARAMS)
        sql_used = renderer._db.execute_query.call_args[0][0]
        assert 'LIMIT 1000' not in sql_used
        assert '"Country" IN %s' in sql_used

    def test_values_are_floats(self):
        rows = [{"Country": "Spain", "total_amount": 999}]
        renderer = _renderer(rows)
        result = renderer._bar_total_amount_by_country(NO_FILTER, ())
        assert isinstance(result["values"][0], float)

    def test_no_filter_passes_empty_params(self):
        renderer = _renderer([])
        renderer._bar_total_amount_by_country(NO_FILTER, ())
        _, params_used = renderer._db.execute_query.call_args[0]
        assert params_used == ()


# ---------------------------------------------------------------------------
# 2. _line_orders_by_week
# ---------------------------------------------------------------------------

class TestLineOrdersByWeek:
    """Tests for _line_orders_by_week — Requirement 5.1."""

    def test_returns_labels_and_values(self):
        rows = [
            {"week_start": datetime(2024, 1, 1), "order_count": 42},
            {"week_start": datetime(2024, 1, 8), "order_count": 37},
        ]
        renderer = _renderer(rows)
        result = renderer._line_orders_by_week(NO_FILTER, ())
        assert result["labels"] == ["2024-01-01", "2024-01-08"]
        assert result["values"] == [42, 37]

    def test_empty_rows_returns_empty_structure(self):
        renderer = _renderer([])
        result = renderer._line_orders_by_week(NO_FILTER, ())
        assert result == {"labels": [], "values": []}

    def test_week_start_formatted_as_yyyy_mm_dd(self):
        rows = [{"week_start": datetime(2024, 6, 3), "order_count": 10}]
        renderer = _renderer(rows)
        result = renderer._line_orders_by_week(NO_FILTER, ())
        assert result["labels"][0] == "2024-06-03"

    def test_values_are_ints(self):
        rows = [{"week_start": datetime(2024, 1, 1), "order_count": 5}]
        renderer = _renderer(rows)
        result = renderer._line_orders_by_week(NO_FILTER, ())
        assert isinstance(result["values"][0], int)

    def test_strips_order_by_suffix(self):
        renderer = _renderer([])
        renderer._line_orders_by_week(WITH_FILTER, PARAMS)
        sql_used = renderer._db.execute_query.call_args[0][0]
        assert 'LIMIT 1000' not in sql_used


# ---------------------------------------------------------------------------
# 3. _pie_order_status
# ---------------------------------------------------------------------------

class TestPieOrderStatus:
    """Tests for _pie_order_status — Requirements 5.1, 5.5."""

    def test_returns_labels_and_values(self):
        rows = [
            {"OrderStatus": "Delivered", "order_count": 300},
            {"OrderStatus": "Shipped", "order_count": 150},
            {"OrderStatus": "Pending", "order_count": 50},
        ]
        renderer = _renderer(rows)
        result = renderer._pie_order_status(NO_FILTER, ())
        assert result["labels"] == ["Delivered", "Shipped", "Pending"]
        assert result["values"] == [300, 150, 50]

    def test_empty_rows_returns_empty_structure(self):
        renderer = _renderer([])
        result = renderer._pie_order_status(NO_FILTER, ())
        assert result == {"labels": [], "values": []}

    def test_values_are_ints(self):
        rows = [{"OrderStatus": "Cancelled", "order_count": 20}]
        renderer = _renderer(rows)
        result = renderer._pie_order_status(NO_FILTER, ())
        assert isinstance(result["values"][0], int)

    def test_strips_order_by_suffix(self):
        renderer = _renderer([])
        renderer._pie_order_status(WITH_FILTER, PARAMS)
        sql_used = renderer._db.execute_query.call_args[0][0]
        assert 'LIMIT 1000' not in sql_used


# ---------------------------------------------------------------------------
# 4. _heatmap_country_category
# ---------------------------------------------------------------------------

class TestHeatmapCountryCategory:
    """Tests for _heatmap_country_category — Requirement 6.1."""

    def test_returns_x_y_z_keys(self):
        rows = [
            {"Country": "Germany", "Category": "Electronics", "order_count": 10},
            {"Country": "Germany", "Category": "Clothing", "order_count": 5},
            {"Country": "France", "Category": "Electronics", "order_count": 8},
        ]
        renderer = _renderer(rows)
        result = renderer._heatmap_country_category(NO_FILTER, ())
        assert set(result.keys()) == {"x", "y", "z"}

    def test_x_contains_sorted_categories(self):
        rows = [
            {"Country": "Germany", "Category": "Electronics", "order_count": 10},
            {"Country": "Germany", "Category": "Clothing", "order_count": 5},
        ]
        renderer = _renderer(rows)
        result = renderer._heatmap_country_category(NO_FILTER, ())
        assert result["x"] == sorted(["Electronics", "Clothing"])

    def test_y_contains_sorted_countries(self):
        rows = [
            {"Country": "Germany", "Category": "Electronics", "order_count": 10},
            {"Country": "France", "Category": "Electronics", "order_count": 8},
        ]
        renderer = _renderer(rows)
        result = renderer._heatmap_country_category(NO_FILTER, ())
        assert result["y"] == ["France", "Germany"]

    def test_z_matrix_correct_values(self):
        rows = [
            {"Country": "Germany", "Category": "Electronics", "order_count": 10},
            {"Country": "Germany", "Category": "Clothing", "order_count": 5},
            {"Country": "France", "Category": "Electronics", "order_count": 8},
        ]
        renderer = _renderer(rows)
        result = renderer._heatmap_country_category(NO_FILTER, ())
        # x = ["Clothing", "Electronics"], y = ["France", "Germany"]
        # France row: Clothing=0, Electronics=8
        # Germany row: Clothing=5, Electronics=10
        assert result["z"][0] == [0, 8]   # France
        assert result["z"][1] == [5, 10]  # Germany

    def test_missing_cell_defaults_to_zero(self):
        rows = [
            {"Country": "Germany", "Category": "Electronics", "order_count": 10},
            {"Country": "France", "Category": "Clothing", "order_count": 3},
        ]
        renderer = _renderer(rows)
        result = renderer._heatmap_country_category(NO_FILTER, ())
        # x = ["Clothing", "Electronics"], y = ["France", "Germany"]
        # France: Clothing=3, Electronics=0
        # Germany: Clothing=0, Electronics=10
        assert result["z"][0] == [3, 0]
        assert result["z"][1] == [0, 10]

    def test_empty_rows_returns_empty_structure(self):
        renderer = _renderer([])
        result = renderer._heatmap_country_category(NO_FILTER, ())
        assert result == {"x": [], "y": [], "z": []}

    def test_strips_order_by_suffix(self):
        renderer = _renderer([])
        renderer._heatmap_country_category(WITH_FILTER, PARAMS)
        sql_used = renderer._db.execute_query.call_args[0][0]
        assert 'LIMIT 1000' not in sql_used


# ---------------------------------------------------------------------------
# 5. _sankey_country_category_status
# ---------------------------------------------------------------------------

class TestSankeyCountryCategoryStatus:
    """Tests for _sankey_country_category_status — Requirement 6.2."""

    def test_empty_rows_returns_empty_nodes_and_links(self):
        renderer = _renderer([])
        result = renderer._sankey_country_category_status(NO_FILTER, ())
        assert "nodes" in result
        assert "links" in result
        assert result["nodes"] == []
        assert result["links"] == []

    def test_returns_nodes_and_links_keys(self):
        rows = [
            {"Country": "Germany", "Category": "Electronics", "OrderStatus": "Shipped", "flow_count": 10},
        ]
        renderer = _renderer(rows)
        result = renderer._sankey_country_category_status(NO_FILTER, ())
        assert set(result.keys()) == {"nodes", "links"}

    def test_strips_order_by_suffix(self):
        renderer = _renderer([])
        renderer._sankey_country_category_status(WITH_FILTER, PARAMS)
        sql_used = renderer._db.execute_query.call_args[0][0]
        assert 'LIMIT 1000' not in sql_used


# ---------------------------------------------------------------------------
# 6. _bubble_category_metrics
# ---------------------------------------------------------------------------

class TestBubbleCategoryMetrics:
    """Tests for _bubble_category_metrics — Requirement 6.3."""

    def test_empty_rows_returns_empty_list(self):
        renderer = _renderer([])
        result = renderer._bubble_category_metrics(NO_FILTER, ())
        assert result == []

    def test_returns_list(self):
        rows = [
            {
                "Category": "Electronics",
                "avg_quantity": 2.50,
                "avg_total_amount": 350.00,
                "avg_shipping_cost": 15.00,
            }
        ]
        renderer = _renderer(rows)
        result = renderer._bubble_category_metrics(NO_FILTER, ())
        assert isinstance(result, list)

    def test_strips_order_by_suffix(self):
        renderer = _renderer([])
        renderer._bubble_category_metrics(WITH_FILTER, PARAMS)
        sql_used = renderer._db.execute_query.call_args[0][0]
        assert 'LIMIT 1000' not in sql_used


# ---------------------------------------------------------------------------
# 7. _treemap_category_brand
# ---------------------------------------------------------------------------

class TestTreemapCategoryBrand:
    """Tests for _treemap_category_brand — Requirement 6.4."""

    def test_returns_list_of_dicts(self):
        rows = [
            {"Category": "Electronics", "Brand": "Sony", "total_amount": 5000.00},
            {"Category": "Electronics", "Brand": "Samsung", "total_amount": 4500.00},
            {"Category": "Clothing", "Brand": "Nike", "total_amount": 3000.00},
        ]
        renderer = _renderer(rows)
        result = renderer._treemap_category_brand(NO_FILTER, ())
        assert isinstance(result, list)
        assert len(result) == 3

    def test_each_item_has_correct_keys(self):
        rows = [{"Category": "Electronics", "Brand": "Sony", "total_amount": 5000.00}]
        renderer = _renderer(rows)
        result = renderer._treemap_category_brand(NO_FILTER, ())
        assert set(result[0].keys()) == {"category", "brand", "total_amount"}

    def test_values_mapped_correctly(self):
        rows = [{"Category": "Electronics", "Brand": "Sony", "total_amount": 5000.75}]
        renderer = _renderer(rows)
        result = renderer._treemap_category_brand(NO_FILTER, ())
        assert result[0]["category"] == "Electronics"
        assert result[0]["brand"] == "Sony"
        assert result[0]["total_amount"] == 5000.75

    def test_total_amount_is_float(self):
        rows = [{"Category": "Electronics", "Brand": "Sony", "total_amount": 5000}]
        renderer = _renderer(rows)
        result = renderer._treemap_category_brand(NO_FILTER, ())
        assert isinstance(result[0]["total_amount"], float)

    def test_empty_rows_returns_empty_list(self):
        renderer = _renderer([])
        result = renderer._treemap_category_brand(NO_FILTER, ())
        assert result == []

    def test_strips_order_by_suffix_from_where(self):
        """The SQL sent to execute_query must not contain the ORDER BY suffix."""
        renderer = _renderer([])
        renderer._treemap_category_brand(WITH_FILTER, PARAMS)
        sql_used = renderer._db.execute_query.call_args[0][0]
        assert 'LIMIT 1000' not in sql_used
        assert '"Country" IN %s' in sql_used

    def test_sql_groups_by_category_and_brand(self):
        renderer = _renderer([])
        renderer._treemap_category_brand(NO_FILTER, ())
        sql_used = renderer._db.execute_query.call_args[0][0]
        assert 'GROUP BY "Category", "Brand"' in sql_used

    def test_sql_orders_by_category_then_total_amount_desc(self):
        renderer = _renderer([])
        renderer._treemap_category_brand(NO_FILTER, ())
        sql_used = renderer._db.execute_query.call_args[0][0]
        assert 'ORDER BY "Category", total_amount DESC' in sql_used

    def test_multiple_brands_per_category(self):
        rows = [
            {"Category": "Electronics", "Brand": "Sony", "total_amount": 5000.00},
            {"Category": "Electronics", "Brand": "Samsung", "total_amount": 4500.00},
        ]
        renderer = _renderer(rows)
        result = renderer._treemap_category_brand(NO_FILTER, ())
        categories = [r["category"] for r in result]
        assert categories == ["Electronics", "Electronics"]

    def test_params_passed_through_to_execute_query(self):
        renderer = _renderer([])
        renderer._treemap_category_brand(WITH_FILTER, PARAMS)
        _, params_used = renderer._db.execute_query.call_args[0]
        assert params_used == PARAMS


# ---------------------------------------------------------------------------
# get_all_chart_payloads — integration smoke test
# ---------------------------------------------------------------------------

class TestGetAllChartPayloads:
    """Smoke tests for get_all_chart_payloads — Requirement 7.3."""

    def test_returns_all_seven_keys(self):
        """get_all_chart_payloads must return a dict with exactly 7 keys."""
        db = MagicMock()
        # Sankey and Bubble still raise NotImplementedError; skip via side_effect
        # We test only that the method calls all 7 private methods.
        renderer = ChartRenderer(db)

        # Patch the two unimplemented methods so the call doesn't blow up
        renderer._sankey_country_category_status = MagicMock(return_value={"nodes": [], "links": []})
        renderer._bubble_category_metrics = MagicMock(return_value=[])
        db.execute_query.return_value = []

        result = renderer.get_all_chart_payloads(NO_FILTER, ())
        expected_keys = {
            "bar_total_amount_by_country",
            "line_orders_by_week",
            "pie_order_status",
            "heatmap_country_category",
            "sankey_country_category_status",
            "bubble_category_metrics",
            "treemap_category_brand",
        }
        assert set(result.keys()) == expected_keys
