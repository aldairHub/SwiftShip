# SwiftShip Logistics Dashboard — Product Overview

SwiftShip Logistics Dashboard is a web application that gives SwiftShip operations analysts visibility into logistics order data. It connects to a PostgreSQL database ("amazon") and lets users explore, filter, and visualize shipment metrics through interactive charts and a paginated data table.

## Core Capabilities

- **KPI Panel** — aggregated metrics: total orders, orders by status, average delivery time
- **Interactive Charts** — order volume over time (line), by region (bar), by status (pie/donut)
- **Order Table** — paginated, sortable table with per-column filtering
- **Filter Engine** — multi-criteria filtering (date range, status, region, carrier) with AND logic
- **Data Export** — CSV download of filtered results (up to 10,000 rows)
- **REST API** — JSON endpoints powering all dynamic frontend interactions

## Target Users

- **Operations Analysts** — primary users; explore and filter order data daily
- **System Administrators** — manage deployment, environment config, and security
- **Frontend Developers** — consume the Flask API layer

## Key Business Rules

- All filters use AND logic; no filter returns up to 1,000 records per request
- CSV export capped at 10,000 rows
- Charts update without full page reload when filters change
- All sensitive config (DB credentials, Flask secret key) must come from environment variables — never hardcoded
