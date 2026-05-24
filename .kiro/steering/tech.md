# Tech Stack

## Backend
- **Language**: Python 3.x
- **Framework**: Flask
- **Database**: PostgreSQL (database name: `amazon`)
- **DB Driver**: psycopg2 (connection pooling, min 2 / max 10 connections)

## Frontend
- **Templating**: Jinja2 (served by Flask)
- **Charting**: Chart.js or Plotly.js
- **Styling**: Responsive layout supporting 1024px, 1280px, 1920px widths

## Configuration
- All sensitive values loaded from environment variables (never hardcoded):
  - `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`
  - `FLASK_SECRET_KEY`
- Missing required env vars at startup → log error + exit with non-zero code

## Security
- Parameterized SQL queries everywhere (no string interpolation in queries)
- Input sanitization before passing to Filter Engine
- Flask debug mode disabled in production
- No stack traces exposed in HTTP responses in production
- CORS headers set to same-origin only

## API Conventions
- All endpoints return `Content-Type: application/json`
- Invalid params → HTTP 400 with descriptive JSON error body
- Server errors → HTTP 500 with generic JSON error body + server-side logging
- Filter params: `date_from`, `date_to`, `status`, `region`, `carrier`

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
flask run

# Run with environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
flask run

# Run tests
pytest

# Run tests with coverage
pytest --cov=app
```
