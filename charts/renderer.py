"""
charts/renderer.py — Chart data aggregation for SwiftShip Logistics Dashboard.

Executes the 7 aggregation queries over the filtered dataset and transforms
the results into JSON-ready payloads for Chart.js / Plotly.js.

Validates: Requirements 5.1, 6.1, 7.3
"""

import logging
import re

from db.connector import DBConnector

logger = logging.getLogger(__name__)


class ChartRenderer:
    """Aggregates order data into chart-ready JSON payloads."""

    def __init__(self, db: DBConnector) -> None:
        self._db = db

    def get_all_chart_payloads(self, where_clause: str, params: tuple) -> dict:
        logger.debug("Building all chart payloads.")
        return {
            "bar_total_amount_by_country": self._bar_total_amount_by_country(where_clause, params),
            "line_orders_by_week": self._line_orders_by_week(where_clause, params),
            "pie_order_status": self._pie_order_status(where_clause, params),
            "heatmap_country_category": self._heatmap_country_category(where_clause, params),
            "sankey_country_category_status": self._sankey_country_category_status(where_clause, params),
            "bubble_category_metrics": self._bubble_category_metrics(where_clause, params),
            "treemap_category_brand": self._treemap_category_brand(where_clause, params),
        }

    def _strip_suffix(self, where: str) -> str:
        return re.sub(r'\s*ORDER BY "OrderDate" DESC LIMIT 1000\s*$', '', where).strip()

    def _bar_total_amount_by_country(self, where: str, params: tuple) -> dict:
        where_only = self._strip_suffix(where)
        sql = (
            'SELECT "Country", ROUND(SUM("TotalAmount")::numeric, 2) AS total_amount '
            'FROM amazon_raw '
            + (where_only + ' ' if where_only else '')
            + 'GROUP BY "Country" ORDER BY total_amount DESC LIMIT 15'
        )
        rows = self._db.execute_query(sql, params)
        if not rows:
            return {"labels": [], "values": []}
        return {
            "labels": [row["Country"] for row in rows],
            "values": [float(row["total_amount"]) for row in rows],
        }

    def _line_orders_by_week(self, where: str, params: tuple) -> dict:
        where_only = self._strip_suffix(where)
        sql = (
            'SELECT DATE_TRUNC(\'week\', "OrderDate"::date) AS week_start, COUNT("OrderID") AS order_count '
            'FROM amazon_raw '
            + (where_only + ' ' if where_only else '')
            + 'GROUP BY week_start ORDER BY week_start ASC'
        )
        rows = self._db.execute_query(sql, params)
        if not rows:
            return {"labels": [], "values": []}
        return {
            "labels": [row["week_start"].strftime("%Y-%m-%d") for row in rows],
            "values": [int(row["order_count"]) for row in rows],
        }

    def _pie_order_status(self, where: str, params: tuple) -> dict:
        where_only = self._strip_suffix(where)
        sql = (
            'SELECT "OrderStatus", COUNT("OrderID") AS order_count '
            'FROM amazon_raw '
            + (where_only + ' ' if where_only else '')
            + 'GROUP BY "OrderStatus" ORDER BY order_count DESC'
        )
        rows = self._db.execute_query(sql, params)
        if not rows:
            return {"labels": [], "values": []}
        return {
            "labels": [row["OrderStatus"] for row in rows],
            "values": [int(row["order_count"]) for row in rows],
        }

    def _heatmap_country_category(self, where: str, params: tuple) -> dict:
        where_only = self._strip_suffix(where)
        sql = (
            'SELECT "Country", "Category", COUNT("OrderID") AS order_count '
            'FROM amazon_raw '
            + (where_only + ' ' if where_only else '')
            + 'GROUP BY "Country", "Category" ORDER BY "Country", "Category"'
        )
        rows = self._db.execute_query(sql, params)
        if not rows:
            return {"x": [], "y": [], "z": []}
        x = sorted({row["Category"] for row in rows})
        y = sorted({row["Country"] for row in rows})
        counts = {(row["Country"], row["Category"]): int(row["order_count"]) for row in rows}
        z = [[counts.get((country, category), 0) for category in x] for country in y]
        return {"x": x, "y": y, "z": z}

    def _sankey_country_category_status(self, where: str, params: tuple) -> dict:
        where_only = self._strip_suffix(where)
        if where_only:
            conditions_only = where_only[6:]
            where_and = "AND " + conditions_only
            combined_params = params + params
        else:
            where_and = ""
            combined_params = params

        sql = (
            'WITH top_countries AS ('
            'SELECT "Country" FROM amazon_raw '
            + (where_only + ' ' if where_only else '')
            + 'GROUP BY "Country" ORDER BY COUNT("OrderID") DESC LIMIT 10) '
            'SELECT o."Country", o."Category", o."OrderStatus", COUNT(o."OrderID") AS flow_count '
            'FROM amazon_raw o '
            'JOIN top_countries tc ON o."Country" = tc."Country" '
            + (where_and + ' ' if where_and else '')
            + 'GROUP BY o."Country", o."Category", o."OrderStatus"'
        )
        rows = self._db.execute_query(sql, combined_params)
        if not rows:
            return {"nodes": [], "links": []}

        seen = {}
        nodes_list = []
        for row in rows:
            for value in (row["Country"], row["Category"], row["OrderStatus"]):
                if value not in seen:
                    seen[value] = True
                    nodes_list.append({"id": value, "label": value})

        link_map: dict = {}
        for row in rows:
            country = row["Country"]
            category = row["Category"]
            status = row["OrderStatus"]
            count = int(row["flow_count"])
            key_cc = (country, category)
            link_map[key_cc] = link_map.get(key_cc, 0) + count
            key_cs = (category, status)
            link_map[key_cs] = link_map.get(key_cs, 0) + count

        links_list = [
            {"source": src, "target": tgt, "value": val}
            for (src, tgt), val in link_map.items()
        ]
        return {"nodes": nodes_list, "links": links_list}

    def _bubble_category_metrics(self, where: str, params: tuple) -> list:
        where_only = self._strip_suffix(where)
        sql = (
            'SELECT "Category", '
            'ROUND(AVG("Quantity")::numeric, 2) AS avg_quantity, '
            'ROUND(AVG("TotalAmount")::numeric, 2) AS avg_total_amount, '
            'ROUND(AVG("ShippingCost")::numeric, 2) AS avg_shipping_cost '
            'FROM amazon_raw '
            + (where_only + ' ' if where_only else '')
            + 'GROUP BY "Category"'
        )
        rows = self._db.execute_query(sql, params)
        if not rows:
            return []
        shipping_costs = [float(row["avg_shipping_cost"]) for row in rows]
        min_cost = min(shipping_costs)
        max_cost = max(shipping_costs)
        result = []
        for row in rows:
            avg_shipping_cost = float(row["avg_shipping_cost"])
            if max_cost == min_cost:
                bubble_size = 35.0
            else:
                bubble_size = round(
                    10 + (avg_shipping_cost - min_cost) / (max_cost - min_cost) * 50, 2
                )
            result.append({
                "category": str(row["Category"]),
                "avg_quantity": float(row["avg_quantity"]),
                "avg_total_amount": float(row["avg_total_amount"]),
                "avg_shipping_cost": avg_shipping_cost,
                "bubble_size": bubble_size,
            })
        return result

    def _treemap_category_brand(self, where: str, params: tuple) -> list:
        where_only = self._strip_suffix(where)
        sql = (
            'SELECT "Category", "Brand", ROUND(SUM("TotalAmount")::numeric, 2) AS total_amount '
            'FROM amazon_raw '
            + (where_only + ' ' if where_only else '')
            + 'GROUP BY "Category", "Brand" ORDER BY "Category", total_amount DESC'
        )
        rows = self._db.execute_query(sql, params)
        if not rows:
            return []
        return [
            {
                "category": row["Category"],
                "brand": row["Brand"],
                "total_amount": float(row["total_amount"]),
            }
            for row in rows
        ]