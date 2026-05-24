# Project Structure

## Expected Layout

```
SwiftShip/
├── app.py                  # Flask app entry point, route registration
├── config.py               # Environment variable loading and validation
├── requirements.txt        # Python dependencies
├── .env.example            # Template for required environment variables
│
├── db/
│   └── connector.py        # DB_Connector: connection pool management (psycopg2)
│
├── filters/
│   └── engine.py           # Filter_Engine: query building and parameterized SQL
│
├── api/
│   ├── orders.py           # /api/orders, /api/orders/summary, /api/orders/export
│   └── charts.py           # /api/orders/charts
│
├── charts/
│   └── renderer.py         # Chart_Renderer: data aggregation for chart payloads
│
├── templates/
│   └── index.html          # Main dashboard Jinja2 template
│
├── static/
│   ├── css/
│   │   └── dashboard.css   # Responsive styles
│   └── js/
│       └── dashboard.js    # Chart rendering, filter form, AJAX calls
│
└── tests/
    ├── test_connector.py
    ├── test_engine.py
    ├── test_api.py
    └── test_charts.py
```

## Component Responsibilities

| Component | Location | Responsibility |
|---|---|---|
| `DB_Connector` | `db/connector.py` | Connection pool, query execution, timeout handling |
| `Filter_Engine` | `filters/engine.py` | Validate inputs, build parameterized SQL WHERE clauses |
| `Chart_Renderer` | `charts/renderer.py` | Aggregate data into chart-ready JSON payloads |
| `API_Layer` | `api/` | Flask blueprints exposing JSON endpoints |
| `Data_Table` | `templates/` + `static/js/` | Paginated/sortable table rendered via API data |
| `KPI_Panel` | `templates/` + `static/js/` | Summary metrics fetched from `/api/orders/summary` |

## Conventions

- **Blueprints**: Register each API module as a Flask Blueprint in `app.py`
- **Error handling**: All exceptions caught at the API layer; never let raw exceptions reach the HTTP response
- **SQL**: All queries use parameterized placeholders (`%s`) — no f-strings or `.format()` in SQL
- **Env vars**: Loaded and validated once in `config.py` at startup; imported by other modules
- **Tests**: Mirror the source structure — one test file per source module
- **Static assets**: JS handles all dynamic behavior (filter submission, chart updates, pagination) via `fetch()` calls to the API layer; no full page reloads for data updates
