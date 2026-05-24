"""
filters/engine.py — Filter parameter parsing and SQL WHERE clause construction
for the SwiftShip Logistics Dashboard.

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 7.1, 9.3, 9.5, 9.6
"""

import logging
import re
from datetime import datetime

from db.connector import FilterValidationError  # noqa: F401 — re-exported for API layer

logger = logging.getLogger(__name__)


class FilterEngine:
    """Validates filter parameters and builds parameterized SQL WHERE clauses."""

    VALID_STATUSES = {'Pending', 'Shipped', 'Delivered', 'Cancelled', 'Returned'}

    def parse_filter_params(self, request_args) -> dict:
        """
        Extract and normalize filter parameters from Flask request.args.

        - date_from, date_to: single string values via .get(), None if absent
        - status, country, category, brand, payment_method, seller_id:
          lists via .getlist(), converted to None if the list is empty

        Returns a normalized dict with all 8 keys always present.

        Validates: Requirements 3.1, 7.1
        """
        date_from = request_args.get('date_from') or None
        date_to = request_args.get('date_to') or None

        def _list_or_none(key: str):
            values = request_args.getlist(key)
            return values if values else None

        params = {
            'date_from': date_from,
            'date_to': date_to,
            'status': _list_or_none('status'),
            'country': _list_or_none('country'),
            'category': _list_or_none('category'),
            'brand': _list_or_none('brand'),
            'payment_method': _list_or_none('payment_method'),
            'seller_id': _list_or_none('seller_id'),
        }

        logger.debug("Parsed filter params: %s", params)
        return params

    # Characters/sequences forbidden in string filter fields (SQL injection prevention)
    _FORBIDDEN_PATTERNS = ("'", '"', ';', '--', '/*', '*/')

    @staticmethod
    def _validate_date(value: str, field_name: str) -> datetime:
        """Validate a date string matches YYYY-MM-DD and is a real calendar date.

        Raises FilterValidationError if the format is wrong or the date is invalid.
        """
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
            raise FilterValidationError("Invalid date format. Expected YYYY-MM-DD")
        try:
            return datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            raise FilterValidationError("Invalid date format. Expected YYYY-MM-DD")

    def _check_injection(self, value: str, param_name: str) -> None:
        """Raise FilterValidationError if *value* contains any forbidden SQL characters."""
        for pattern in self._FORBIDDEN_PATTERNS:
            if pattern in value:
                raise FilterValidationError(
                    f"Invalid characters in {param_name}: {value}"
                )

    def build_where_clause(
        self,
        date_from: 'str | None',
        date_to: 'str | None',
        status: 'list[str] | None',
        country: 'list[str] | None',
        category: 'list[str] | None',
        brand: 'list[str] | None',
        payment_method: 'list[str] | None',
        seller_id: 'list[str] | None',
    ) -> 'tuple[str, tuple]':
        """
        Validate all parameters and build a parameterized SQL WHERE clause.

        Validation rules:
        - date_from / date_to: must match ^\\d{4}-\\d{2}-\\d{2}$ and be a real date.
        - date_from <= date_to when both are provided.
        - Each status value must be in VALID_STATUSES.
        - country, category, brand, payment_method, seller_id: each value must not
          contain ', ", ;, --, /*, or */.

        Returns (where_clause_str, params_tuple).
        If no filters are active returns ('ORDER BY "OrderDate" DESC LIMIT 1000', ()).
        Raises FilterValidationError (→ HTTP 400) for any invalid parameter.
        Never interpolates values directly into SQL.

        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 9.3, 9.5, 9.6
        """
        # ------------------------------------------------------------------
        # 1. Date format validation
        # ------------------------------------------------------------------
        date_from_dt = None
        date_to_dt = None

        if date_from is not None:
            date_from_dt = self._validate_date(date_from, 'date_from')

        if date_to is not None:
            date_to_dt = self._validate_date(date_to, 'date_to')

        # ------------------------------------------------------------------
        # 2. Date range validation
        # ------------------------------------------------------------------
        if date_from_dt is not None and date_to_dt is not None:
            if date_from_dt > date_to_dt:
                raise FilterValidationError(
                    "date_from must be earlier than or equal to date_to"
                )

        # ------------------------------------------------------------------
        # 3. Status validation
        # ------------------------------------------------------------------
        if status is not None:
            for value in status:
                if value not in self.VALID_STATUSES:
                    raise FilterValidationError(f"Invalid status value: {value}")

        # ------------------------------------------------------------------
        # 4. SQL injection check for string list fields
        # ------------------------------------------------------------------
        string_list_fields = {
            'country': country,
            'category': category,
            'brand': brand,
            'payment_method': payment_method,
            'seller_id': seller_id,
        }
        for param_name, values in string_list_fields.items():
            if values is not None:
                for value in values:
                    self._check_injection(value, param_name)

        # ------------------------------------------------------------------
        # 5. Build WHERE clause
        # ------------------------------------------------------------------
        conditions: list[str] = []
        params: list = []

        if date_from is not None:
            conditions.append('"OrderDate" >= %s')
            params.append(date_from)

        if date_to is not None:
            conditions.append('"OrderDate" <= %s')
            params.append(date_to)

        if status is not None:
            conditions.append('"OrderStatus" IN %s')
            params.append(tuple(status))

        if country is not None:
            conditions.append('"Country" IN %s')
            params.append(tuple(country))

        if category is not None:
            conditions.append('"Category" IN %s')
            params.append(tuple(category))

        if brand is not None:
            conditions.append('"Brand" IN %s')
            params.append(tuple(brand))

        if payment_method is not None:
            conditions.append('"PaymentMethod" IN %s')
            params.append(tuple(payment_method))

        if seller_id is not None:
            conditions.append('"SellerID" IN %s')
            params.append(tuple(seller_id))

        # ------------------------------------------------------------------
        # 6. Return result
        # ------------------------------------------------------------------
        suffix = 'ORDER BY "OrderDate" DESC LIMIT 1000'

        if not conditions:
            return (suffix, ())

        where_clause = 'WHERE ' + ' AND '.join(conditions) + ' ' + suffix
        return (where_clause, tuple(params))
