"""
tests/test_engine.py — Unit tests for FilterEngine.parse_filter_params.

Validates: Requirements 3.1, 7.1
"""

import os
import sys

import pytest
from werkzeug.datastructures import ImmutableMultiDict

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

from filters.engine import FilterEngine  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _args(**kwargs):
    """Build a Werkzeug ImmutableMultiDict from keyword arguments.

    Pass list values as actual lists to simulate multi-value query params:
        _args(status=['Shipped', 'Delivered'])
    """
    pairs = []
    for key, value in kwargs.items():
        if isinstance(value, list):
            for v in value:
                pairs.append((key, v))
        else:
            pairs.append((key, value))
    return ImmutableMultiDict(pairs)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestParseFilterParams:
    """Tests for FilterEngine.parse_filter_params — Requirements 3.1, 7.1."""

    def setup_method(self):
        self.engine = FilterEngine()

    # --- Always returns all 8 keys ---

    def test_empty_args_returns_all_keys_as_none(self):
        """All 8 keys must be present and None when no params are provided."""
        result = self.engine.parse_filter_params(_args())
        expected_keys = {
            'date_from', 'date_to', 'status', 'country',
            'category', 'brand', 'payment_method', 'seller_id',
        }
        assert set(result.keys()) == expected_keys
        for key in expected_keys:
            assert result[key] is None, f"Expected {key} to be None, got {result[key]!r}"

    # --- date_from / date_to as single strings ---

    def test_date_from_extracted_as_string(self):
        result = self.engine.parse_filter_params(_args(date_from='2024-01-01'))
        assert result['date_from'] == '2024-01-01'

    def test_date_to_extracted_as_string(self):
        result = self.engine.parse_filter_params(_args(date_to='2024-12-31'))
        assert result['date_to'] == '2024-12-31'

    def test_both_dates_extracted(self):
        result = self.engine.parse_filter_params(
            _args(date_from='2024-01-01', date_to='2024-06-30')
        )
        assert result['date_from'] == '2024-01-01'
        assert result['date_to'] == '2024-06-30'

    def test_absent_date_from_is_none(self):
        result = self.engine.parse_filter_params(_args(date_to='2024-12-31'))
        assert result['date_from'] is None

    def test_absent_date_to_is_none(self):
        result = self.engine.parse_filter_params(_args(date_from='2024-01-01'))
        assert result['date_to'] is None

    # --- List params: single value ---

    def test_single_status_returned_as_list(self):
        result = self.engine.parse_filter_params(_args(status='Shipped'))
        assert result['status'] == ['Shipped']

    def test_single_country_returned_as_list(self):
        result = self.engine.parse_filter_params(_args(country='Germany'))
        assert result['country'] == ['Germany']

    def test_single_category_returned_as_list(self):
        result = self.engine.parse_filter_params(_args(category='Electronics'))
        assert result['category'] == ['Electronics']

    def test_single_brand_returned_as_list(self):
        result = self.engine.parse_filter_params(_args(brand='TechBrand'))
        assert result['brand'] == ['TechBrand']

    def test_single_payment_method_returned_as_list(self):
        result = self.engine.parse_filter_params(_args(payment_method='Credit Card'))
        assert result['payment_method'] == ['Credit Card']

    def test_single_seller_id_returned_as_list(self):
        result = self.engine.parse_filter_params(_args(seller_id='S001'))
        assert result['seller_id'] == ['S001']

    # --- List params: multiple values ---

    def test_multiple_status_values_returned_as_list(self):
        result = self.engine.parse_filter_params(
            _args(status=['Shipped', 'Delivered', 'Pending'])
        )
        assert result['status'] == ['Shipped', 'Delivered', 'Pending']

    def test_multiple_country_values_returned_as_list(self):
        result = self.engine.parse_filter_params(
            _args(country=['Germany', 'France', 'Spain'])
        )
        assert result['country'] == ['Germany', 'France', 'Spain']

    def test_multiple_seller_ids_returned_as_list(self):
        result = self.engine.parse_filter_params(
            _args(seller_id=['S001', 'S002', 'S003'])
        )
        assert result['seller_id'] == ['S001', 'S002', 'S003']

    # --- Empty list → None ---

    def test_absent_status_is_none(self):
        result = self.engine.parse_filter_params(_args())
        assert result['status'] is None

    def test_absent_country_is_none(self):
        result = self.engine.parse_filter_params(_args())
        assert result['country'] is None

    def test_absent_category_is_none(self):
        result = self.engine.parse_filter_params(_args())
        assert result['category'] is None

    def test_absent_brand_is_none(self):
        result = self.engine.parse_filter_params(_args())
        assert result['brand'] is None

    def test_absent_payment_method_is_none(self):
        result = self.engine.parse_filter_params(_args())
        assert result['payment_method'] is None

    def test_absent_seller_id_is_none(self):
        result = self.engine.parse_filter_params(_args())
        assert result['seller_id'] is None

    # --- Combined filters ---

    def test_combined_filters_all_present(self):
        result = self.engine.parse_filter_params(_args(
            date_from='2024-01-01',
            date_to='2024-12-31',
            status=['Shipped', 'Delivered'],
            country='Germany',
            category='Electronics',
            brand='TechBrand',
            payment_method='Credit Card',
            seller_id='S001',
        ))
        assert result['date_from'] == '2024-01-01'
        assert result['date_to'] == '2024-12-31'
        assert result['status'] == ['Shipped', 'Delivered']
        assert result['country'] == ['Germany']
        assert result['category'] == ['Electronics']
        assert result['brand'] == ['TechBrand']
        assert result['payment_method'] == ['Credit Card']
        assert result['seller_id'] == ['S001']




# ---------------------------------------------------------------------------
# Tests for FilterEngine.build_where_clause
# Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 9.3, 9.5, 9.6
# ---------------------------------------------------------------------------

from db.connector import FilterValidationError  # noqa: E402


class TestBuildWhereClause:
    """Tests for FilterEngine.build_where_clause."""

    def setup_method(self):
        self.engine = FilterEngine()

    def _call(self, **kwargs):
        """Helper: call build_where_clause with all params defaulting to None."""
        defaults = dict(
            date_from=None, date_to=None, status=None,
            country=None, category=None, brand=None,
            payment_method=None, seller_id=None,
        )
        defaults.update(kwargs)
        return self.engine.build_where_clause(**defaults)

    # -----------------------------------------------------------------------
    # No-filter case
    # -----------------------------------------------------------------------

    def test_no_filters_returns_order_by_only(self):
        """With no filters the clause must be just ORDER BY … LIMIT 1000 and empty params."""
        clause, params = self._call()
        assert clause == 'ORDER BY "OrderDate" DESC LIMIT 1000'
        assert params == ()

    # -----------------------------------------------------------------------
    # Date format validation (Req 3.2)
    # -----------------------------------------------------------------------

    def test_valid_date_from_accepted(self):
        clause, params = self._call(date_from='2024-01-01')
        assert '"OrderDate" >= %s' in clause
        assert '2024-01-01' in params

    def test_valid_date_to_accepted(self):
        clause, params = self._call(date_to='2024-12-31')
        assert '"OrderDate" <= %s' in clause
        assert '2024-12-31' in params

    def test_date_from_wrong_format_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid date format"):
            self._call(date_from='01-01-2024')

    def test_date_to_wrong_format_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid date format"):
            self._call(date_to='2024/12/31')

    def test_date_from_invalid_calendar_date_raises(self):
        """Month 13 passes the regex but fails strptime — must still raise."""
        with pytest.raises(FilterValidationError, match="Invalid date format"):
            self._call(date_from='2024-13-01')

    def test_date_from_invalid_day_raises(self):
        """Day 32 passes the regex but fails strptime."""
        with pytest.raises(FilterValidationError, match="Invalid date format"):
            self._call(date_from='2024-01-32')

    def test_date_to_invalid_calendar_date_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid date format"):
            self._call(date_to='2024-02-30')

    def test_date_partial_string_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid date format"):
            self._call(date_from='2024-01')

    # -----------------------------------------------------------------------
    # Date range validation (Req 3.3)
    # -----------------------------------------------------------------------

    def test_date_from_equal_to_date_to_accepted(self):
        clause, params = self._call(date_from='2024-06-15', date_to='2024-06-15')
        assert 'WHERE' in clause
        assert '2024-06-15' in params

    def test_date_from_before_date_to_accepted(self):
        clause, params = self._call(date_from='2024-01-01', date_to='2024-12-31')
        assert 'WHERE' in clause

    def test_date_from_after_date_to_raises(self):
        with pytest.raises(FilterValidationError, match="date_from must be earlier than or equal to date_to"):
            self._call(date_from='2024-12-31', date_to='2024-01-01')

    def test_only_date_from_no_range_check(self):
        """Single date without date_to should not trigger range validation."""
        clause, params = self._call(date_from='2024-06-01')
        assert '"OrderDate" >= %s' in clause

    def test_only_date_to_no_range_check(self):
        clause, params = self._call(date_to='2024-06-01')
        assert '"OrderDate" <= %s' in clause

    # -----------------------------------------------------------------------
    # Status validation (Req 3.4)
    # -----------------------------------------------------------------------

    def test_all_valid_statuses_accepted(self):
        for status in ('Pending', 'Shipped', 'Delivered', 'Cancelled', 'Returned'):
            clause, params = self._call(status=[status])
            assert '"OrderStatus" IN %s' in clause

    def test_multiple_valid_statuses_accepted(self):
        clause, params = self._call(status=['Shipped', 'Delivered'])
        assert '"OrderStatus" IN %s' in clause
        assert ('Shipped', 'Delivered') in params

    def test_invalid_status_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid status value: Unknown"):
            self._call(status=['Unknown'])

    def test_invalid_status_mixed_with_valid_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid status value: BadStatus"):
            self._call(status=['Shipped', 'BadStatus'])

    def test_empty_string_status_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid status value:"):
            self._call(status=[''])

    def test_case_sensitive_status_raises(self):
        """Status values are case-sensitive; 'shipped' is not valid."""
        with pytest.raises(FilterValidationError, match="Invalid status value: shipped"):
            self._call(status=['shipped'])

    # -----------------------------------------------------------------------
    # SQL injection prevention (Req 9.3, 9.5, 9.6)
    # -----------------------------------------------------------------------

    def test_single_quote_in_country_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid characters in country"):
            self._call(country=["O'Brien"])

    def test_double_quote_in_category_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid characters in category"):
            self._call(category=['Elec"tronics'])

    def test_semicolon_in_brand_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid characters in brand"):
            self._call(brand=['Brand; DROP TABLE orders--'])

    def test_double_dash_in_payment_method_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid characters in payment_method"):
            self._call(payment_method=['Credit--Card'])

    def test_block_comment_open_in_seller_id_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid characters in seller_id"):
            self._call(seller_id=['S001/*'])

    def test_block_comment_close_in_country_raises(self):
        with pytest.raises(FilterValidationError, match="Invalid characters in country"):
            self._call(country=['Ger*/many'])

    def test_clean_values_accepted(self):
        """Values without forbidden characters must pass through."""
        clause, params = self._call(
            country=['Germany'],
            category=['Electronics'],
            brand=['TechBrand'],
            payment_method=['Credit Card'],
            seller_id=['S001'],
        )
        assert 'WHERE' in clause

    # -----------------------------------------------------------------------
    # WHERE clause construction (Req 3.5 – 3.9)
    # -----------------------------------------------------------------------

    def test_single_country_builds_in_clause(self):
        clause, params = self._call(country=['Germany'])
        assert '"Country" IN %s' in clause
        assert ('Germany',) in params

    def test_multiple_countries_build_in_clause(self):
        clause, params = self._call(country=['Germany', 'France'])
        assert '"Country" IN %s' in clause
        assert ('Germany', 'France') in params

    def test_category_builds_in_clause(self):
        clause, params = self._call(category=['Electronics'])
        assert '"Category" IN %s' in clause

    def test_brand_builds_in_clause(self):
        clause, params = self._call(brand=['TechBrand'])
        assert '"Brand" IN %s' in clause

    def test_payment_method_builds_in_clause(self):
        clause, params = self._call(payment_method=['Credit Card'])
        assert '"PaymentMethod" IN %s' in clause

    def test_seller_id_builds_in_clause(self):
        clause, params = self._call(seller_id=['S001'])
        assert '"SellerID" IN %s' in clause

    def test_all_filters_combined(self):
        clause, params = self._call(
            date_from='2024-01-01',
            date_to='2024-12-31',
            status=['Shipped'],
            country=['Germany'],
            category=['Electronics'],
            brand=['TechBrand'],
            payment_method=['Credit Card'],
            seller_id=['S001'],
        )
        assert clause.startswith('WHERE ')
        assert '"OrderDate" >= %s' in clause
        assert '"OrderDate" <= %s' in clause
        assert '"OrderStatus" IN %s' in clause
        assert '"Country" IN %s' in clause
        assert '"Category" IN %s' in clause
        assert '"Brand" IN %s' in clause
        assert '"PaymentMethod" IN %s' in clause
        assert '"SellerID" IN %s' in clause
        assert ' AND ' in clause

    def test_conditions_joined_with_and(self):
        clause, _ = self._call(date_from='2024-01-01', country=['Germany'])
        # Two conditions → one AND
        assert clause.count(' AND ') == 1

    def test_order_by_always_appended(self):
        """ORDER BY … LIMIT 1000 must appear in every output."""
        for kwargs in [
            {},
            {'date_from': '2024-01-01'},
            {'status': ['Shipped']},
            {'country': ['Germany'], 'brand': ['TechBrand']},
        ]:
            clause, _ = self._call(**kwargs)
            assert 'ORDER BY "OrderDate" DESC LIMIT 1000' in clause

    # -----------------------------------------------------------------------
    # Return type guarantees
    # -----------------------------------------------------------------------

    def test_return_is_two_tuple(self):
        result = self._call()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_params_is_tuple(self):
        _, params = self._call(date_from='2024-01-01')
        assert isinstance(params, tuple)

    def test_no_filters_params_is_empty_tuple(self):
        _, params = self._call()
        assert params == ()

    def test_clause_is_string(self):
        clause, _ = self._call()
        assert isinstance(clause, str)
