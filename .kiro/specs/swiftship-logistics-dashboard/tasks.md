# Plan de Implementación: SwiftShip Logistics Dashboard

## Descripción General

Implementación incremental del dashboard logístico de SwiftShip sobre Flask + Python + PostgreSQL. Las tareas siguen el orden de dependencias naturales: configuración y capa de datos primero, lógica de negocio después, API encima, y finalmente la interfaz de usuario. Cada tarea produce código funcional que se integra con el paso anterior.

---

## Tareas

- [x] 1. Configuración del proyecto y estructura base
  - Crear `requirements.txt` con las dependencias exactas: `Flask`, `psycopg2-binary`, `python-dotenv`
  - Crear `.env.example` con las variables requeridas: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `FLASK_SECRET_KEY`, `FLASK_ENV`
  - Crear los directorios vacíos con `__init__.py`: `db/`, `filters/`, `api/`, `charts/`
  - _Requisitos: 9.1, 9.2_

- [x] 2. Implementar `config.py` — carga y validación de variables de entorno
  - [x] 2.1 Implementar la función de carga de configuración en `config.py`
    - Leer `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `FLASK_SECRET_KEY` desde `os.environ`
    - Si alguna variable está ausente, registrar `"Missing required environment variable: <nombre>"` y llamar `sys.exit(1)`
    - Exponer las variables como constantes del módulo para que otros módulos las importen
    - _Requisitos: 1.1, 9.1, 9.2_

- [x] 3. Implementar `db/connector.py` — pool de conexiones y ejecución de consultas
  - [x] 3.1 Implementar la clase `DBConnector` con inicialización del pool
    - Usar `psycopg2.pool.ThreadedConnectionPool(minconn=2, maxconn=10)` con los parámetros de `config.py`
    - Configurar `connection_timeout=5` segundos para espera de conexión del pool
    - Lanzar `SystemExit(1)` si el pool no puede inicializarse (variables faltantes ya manejadas en `config.py`)
    - _Requisitos: 1.1, 1.2_
  - [x] 3.2 Implementar la jerarquía de excepciones personalizadas en `db/connector.py`
    - Definir `SwiftShipError(Exception)`, `FilterValidationError`, `QueryTimeoutError`, `PoolExhaustedError`, `ConnectionError` como subclases
    - _Requisitos: 1.5, 1.7_
  - [x] 3.3 Implementar `DBConnector.execute_query(sql, params)` con manejo completo de errores
    - Obtener conexión del pool; si no hay disponible en 5 s, lanzar `PoolExhaustedError("Connection pool exhausted")`
    - Antes de ejecutar, verificar `conn.closed` y ejecutar `SELECT 1` de prueba; reconectar si la conexión lleva inactiva >300 s
    - Establecer `SET LOCAL statement_timeout = '30000'` (30 s) por sesión antes de cada consulta
    - Si se supera el timeout, capturar la excepción psycopg2 correspondiente y lanzar `QueryTimeoutError("Query timeout after 30 seconds")`
    - Retornar lista de dicts usando `cursor.description` para los nombres de columna
    - En mensajes de error, incluir tipo de excepción y `host:port`; nunca incluir el valor de `DB_PASSWORD`
    - Devolver siempre la conexión al pool en el bloque `finally`
    - _Requisitos: 1.3, 1.4, 1.5, 1.6, 1.7_
  - [x] 3.4 Implementar `DBConnector.close()` para cerrar el pool limpiamente
    - Llamar a `pool.closeall()` y registrar el cierre en el log
    - _Requisitos: 1.2_

- [x] 4. Implementar `filters/engine.py` — validación y construcción de cláusulas SQL
  - [x] 4.1 Implementar `FilterEngine.parse_filter_params(request_args)` 
    - Extraer `date_from`, `date_to` como strings únicos
    - Extraer `status`, `country`, `category`, `brand`, `payment_method`, `seller_id` como listas usando `getlist()`
    - Retornar dict normalizado con `None` para parámetros ausentes y listas vacías convertidas a `None`
    - _Requisitos: 3.1, 7.1_
  - [x] 4.2 Implementar `FilterEngine.build_where_clause(...)` con validación completa
    - Validar `date_from` y `date_to` con regex `^\d{4}-\d{2}-\d{2}$` y `datetime.strptime`; lanzar `FilterValidationError("Invalid date format. Expected YYYY-MM-DD")` si el formato es inválido
    - Validar que `date_from <= date_to`; lanzar `FilterValidationError("date_from must be earlier than or equal to date_to")` si no
    - Validar cada valor de `status` contra `VALID_STATUSES = {'Pending','Shipped','Delivered','Cancelled','Returned'}`; lanzar `FilterValidationError("Invalid status value: <valor>")` si no pertenece
    - Para `country`, `category`, `brand`, `payment_method`, `seller_id`: rechazar cualquier valor que contenga `'`, `"`, `;`, `--`, `/*`, `*/`; lanzar `FilterValidationError` con mensaje descriptivo
    - Construir la cláusula `WHERE` acumulando condiciones con `%s` parametrizados; usar `IN %s` con tupla para listas
    - Añadir `ORDER BY "OrderDate" DESC LIMIT 1000` al final de la cláusula
    - Retornar `(where_clause_str, params_tuple)`; si no hay filtros, retornar `("ORDER BY \"OrderDate\" DESC LIMIT 1000", ())`
    - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 9.3, 9.5, 9.6_

- [x] 5. Implementar `charts/renderer.py` — agregaciones para los 7 payloads de gráficos
  - [x] 5.1 Implementar la clase `ChartRenderer` con constructor y método `get_all_chart_payloads`
    - Constructor recibe instancia de `DBConnector`
    - `get_all_chart_payloads(where_clause, params)` llama a los 7 métodos privados y retorna el dict con las 7 claves
    - _Requisitos: 5.1, 6.1, 7.3_
  - [x] 5.2 Implementar `_bar_total_amount_by_country(where, params)`
    - SQL: `SELECT "Country", ROUND(SUM("TotalAmount")::numeric, 2) AS total_amount FROM orders {WHERE} GROUP BY "Country" ORDER BY total_amount DESC LIMIT 15`
    - Retornar `{"labels": [...], "values": [...]}`
    - _Requisitos: 5.1_
  - [x] 5.3 Implementar `_line_orders_by_week(where, params)`
    - SQL: `SELECT DATE_TRUNC('week', "OrderDate") AS week_start, COUNT("OrderID") AS order_count FROM orders {WHERE} GROUP BY week_start ORDER BY week_start ASC`
    - Formatear `week_start` como string `YYYY-MM-DD`
    - Retornar `{"labels": [...], "values": [...]}`
    - _Requisitos: 5.1_
  - [x] 5.4 Implementar `_pie_order_status(where, params)`
    - SQL: `SELECT "OrderStatus", COUNT("OrderID") AS order_count FROM orders {WHERE} GROUP BY "OrderStatus" ORDER BY order_count DESC`
    - Retornar `{"labels": [...], "values": [...]}`
    - _Requisitos: 5.1, 5.5_
  - [x] 5.5 Implementar `_heatmap_country_category(where, params)`
    - SQL: `SELECT "Country", "Category", COUNT("OrderID") AS order_count FROM orders {WHERE} GROUP BY "Country", "Category" ORDER BY "Country", "Category"`
    - Construir matrices `x` (categorías únicas), `y` (países únicos), `z` (matriz 2D de conteos, 0 para celdas sin datos)
    - Retornar `{"x": [...], "y": [...], "z": [[...], ...]}`
    - _Requisitos: 6.1_
  - [x] 5.6 Implementar `_sankey_country_category_status(where, params)`
    - SQL con CTE `top_countries` para los 10 países con mayor `COUNT(OrderID)`, luego join con la tabla principal para obtener flujos `Country → Category → OrderStatus`
    - Construir lista de nodos únicos y lista de links con `source`, `target`, `value`
    - Retornar `{"nodes": [...], "links": [...]}`
    - _Requisitos: 6.2_
  - [x] 5.7 Implementar `_bubble_category_metrics(where, params)`
    - SQL: `SELECT "Category", ROUND(AVG("Quantity")::numeric,2), ROUND(AVG("TotalAmount")::numeric,2), ROUND(AVG("ShippingCost")::numeric,2) FROM orders {WHERE} GROUP BY "Category"`
    - Normalizar `avg_shipping_cost` al rango de píxeles `[10, 60]` para `bubble_size`
    - Retornar lista de objetos `{"category", "avg_quantity", "avg_total_amount", "avg_shipping_cost", "bubble_size"}`
    - _Requisitos: 6.3_
  - [x] 5.8 Implementar `_treemap_category_brand(where, params)`
    - SQL: `SELECT "Category", "Brand", ROUND(SUM("TotalAmount")::numeric,2) AS total_amount FROM orders {WHERE} GROUP BY "Category", "Brand" ORDER BY "Category", total_amount DESC`
    - Retornar lista de objetos `{"category", "brand", "total_amount"}`
    - _Requisitos: 6.4_

- [ ] 6. Implementar `api/orders.py` — Blueprint con los 3 endpoints de pedidos
  - [-] 6.1 Implementar el Blueprint `orders_bp` y el endpoint `GET /api/orders`
    - Registrar `orders_bp = Blueprint('orders', __name__, url_prefix='/api/orders')`
    - Parsear parámetros con `filter_engine.parse_filter_params(request.args)`
    - Construir cláusula WHERE con `filter_engine.build_where_clause(**params)`
    - Ejecutar `SELECT OrderID, OrderDate, CustomerName, ProductName, Category, Brand, Quantity, UnitPrice, Discount, Tax, ShippingCost, TotalAmount, PaymentMethod, OrderStatus, City, State, Country FROM orders {WHERE}` con `db.execute_query`
    - Retornar `jsonify(rows), 200`
    - Manejar `FilterValidationError` → 400, `QueryTimeoutError` → 504, `PoolExhaustedError` → 503, `Exception` → 500 con log del traceback
    - _Requisitos: 7.1, 7.5, 7.6, 7.7, 7.9_
  - [-] 6.2 Implementar el endpoint `GET /api/orders/summary`
    - Ejecutar las 7 consultas SQL de KPIs definidas en el diseño (total_revenue, avg_shipping_cost_by_country top 5, cancellation_rate_by_category, avg_discount_pct, top_brand_by_quantity, top_payment_method, discount_cancellation_correlation con `CORR()`)
    - Manejar el caso de conjunto vacío: retornar `0.00`, `[]`, `0.0`, `null`, `null`, `null` según corresponda sin errores de división por cero (usar `NULLIF` en SQL)
    - Construir y retornar el objeto JSON con exactamente las 7 claves especificadas en el diseño
    - Aplicar el mismo patrón de manejo de errores que 6.1
    - _Requisitos: 2.1, 2.2, 7.2, 7.5, 7.6, 7.7_
  - [-] 6.3 Implementar el endpoint `GET /api/orders/export`
    - Ejecutar la consulta de exportación con `LIMIT 10001` para detectar truncamiento (las 20 columnas incluyendo `CustomerID`, `ProductID`, `SellerID`)
    - Si el resultado tiene más de 10,000 filas, tomar solo las primeras 10,000 y añadir header `X-Export-Truncated: true`
    - Generar el CSV usando `csv.writer` sobre un `io.StringIO` con la fila de encabezado exacta del requisito 8.1
    - Formatear `Discount` como decimal `[0,1]` con 2 decimales; formatear `UnitPrice`, `ShippingCost`, `Tax`, `TotalAmount` con 2 decimales
    - Retornar respuesta con `Content-Type: text/csv` y `Content-Disposition: attachment; filename="swiftship_orders_export.csv"`
    - Si el conjunto filtrado tiene 0 registros, retornar CSV con solo la fila de encabezado y HTTP 200
    - _Requisitos: 7.4, 7.7, 7.8, 8.1, 8.2, 8.3, 8.4_

- [ ] 7. Implementar `api/charts.py` — Blueprint con el endpoint de gráficos
  - [ ] 7.1 Implementar el Blueprint `charts_bp` y el endpoint `GET /api/orders/charts`
    - Registrar `charts_bp = Blueprint('charts', __name__, url_prefix='/api/orders')`
    - Parsear y validar parámetros con `filter_engine`
    - Llamar a `chart_renderer.get_all_chart_payloads(where_clause, params)`
    - Retornar `jsonify(payload), 200` con el dict de 7 claves
    - Aplicar el mismo patrón de manejo de errores que los endpoints de `orders_bp`
    - _Requisitos: 7.3, 7.5, 7.6, 7.7_

- [~] 8. Implementar `app.py` — punto de entrada Flask y registro de Blueprints
  - Crear la aplicación Flask, cargar `SECRET_KEY` desde `config.py`
  - Registrar `orders_bp` y `charts_bp` con `app.register_blueprint()`
  - Añadir la ruta raíz `GET /` que sirve `templates/index.html` con `render_template`
  - Configurar headers CORS de mismo origen en un `@app.after_request` hook
  - Deshabilitar el modo debug cuando `FLASK_ENV=production`
  - Instanciar `DBConnector`, `FilterEngine` y `ChartRenderer` una sola vez y pasarlos a los blueprints (o usar el contexto de aplicación)
  - _Requisitos: 7.9, 9.4_

- [~] 9. Punto de control — verificar que la API responde correctamente
  - Asegurarse de que `flask run` arranca sin errores con las variables de entorno configuradas
  - Verificar que `GET /api/orders` retorna JSON con las columnas correctas
  - Verificar que `GET /api/orders/summary` retorna las 7 claves
  - Verificar que `GET /api/orders/charts` retorna las 7 claves de gráficos
  - Verificar que parámetros inválidos retornan HTTP 400 con mensaje descriptivo
  - Preguntar al usuario si hay dudas antes de continuar con el frontend.

- [ ] 10. Implementar `templates/index.html` — plantilla Jinja2 del dashboard
  - [~] 10.1 Crear la estructura HTML base del dashboard
    - Incluir `<head>` con meta viewport, título "SwiftShip Logistics Dashboard", enlace a `dashboard.css`
    - Crear el formulario de filtros con campos: `date_from`, `date_to`, `status` (select múltiple con los 5 valores válidos), `country`, `category`, `brand`, `payment_method`, `seller_id`; botones "Aplicar" y "Limpiar"
    - Crear el área del KPI Panel con 7 tarjetas (una por métrica), cada una con un `<div>` para el spinner y otro para el valor
    - _Requisitos: 2.1, 3.1_
  - [~] 10.2 Crear la estructura HTML de la tabla de pedidos y los controles de paginación
    - Crear `<table>` con `<thead>` que contenga exactamente las 17 columnas en el orden especificado en el requisito 4.1; marcar como ordenables `OrderDate`, `TotalAmount`, `ShippingCost`, `Quantity`, `Discount` con atributo `data-sort`
    - Crear el selector de tamaño de página (10/25/50), el texto de conteo `"Mostrando X–Y de Z pedidos"` y los controles de navegación de páginas
    - Crear el área de mensaje vacío `"No se encontraron pedidos con los filtros seleccionados."`
    - _Requisitos: 4.1, 4.2, 4.5, 4.6_
  - [~] 10.3 Crear la estructura HTML de los contenedores de gráficos
    - Crear 7 contenedores `<canvas>` o `<div>` con IDs únicos para cada gráfico: `chart-bar`, `chart-line`, `chart-pie`, `chart-heatmap`, `chart-sankey`, `chart-bubble`, `chart-treemap`
    - Incluir en cada contenedor un `<div>` para el mensaje `"Sin datos para mostrar con los filtros actuales."`
    - Incluir los scripts de Chart.js / Plotly.js y el enlace a `dashboard.js` al final del `<body>`
    - Añadir el botón de exportación CSV con id `btn-export`
    - _Requisitos: 5.1, 5.3, 6.1, 6.2, 6.3, 6.4, 8.5_

- [ ] 11. Implementar `static/js/dashboard.js` — módulos JavaScript del frontend
  - [~] 11.1 Implementar `FilterManager`
    - `getActiveFilters()`: serializa todos los campos del formulario en un objeto; usa `Array.from(select.selectedOptions)` para selects múltiples
    - `buildQueryString(filters)`: construye `URLSearchParams` con soporte para parámetros multi-valor (append por cada valor de lista)
    - `bindFormEvents()`: escucha el evento `submit` del formulario, llama `event.preventDefault()`, llama `FilterManager.getActiveFilters()` y dispara la actualización del dashboard; escucha el botón "Limpiar" para resetear el formulario
    - `resetPagination()`: notifica a `TableManager` para volver a página 1
    - _Requisitos: 3.1, 4.8_
  - [~] 11.2 Implementar `TableManager`
    - Estado interno: `{ currentPage: 1, pageSize: 25, sortColumn: 'OrderDate', sortDirection: 'desc', totalRecords: 0 }`
    - `fetch(filters)`: construye URL `/api/orders` con filtros + `sort_by`, `sort_dir`, `page`, `page_size`; muestra spinner; en error HTTP muestra `"Error al cargar los datos. Intente nuevamente."`
    - `render(orders, total)`: genera filas `<tr>` con las 17 columnas; formatea `Discount` como `"X.X%"`, valores monetarios como `"$X.XX"`; si `orders` está vacío muestra el mensaje de sin resultados
    - `renderPagination(total)`: calcula `ceil(total/pageSize)` páginas; genera controles; muestra `"Mostrando X–Y de Z pedidos"`
    - `bindSortHeaders()`: ciclo asc → desc → asc al hacer clic en encabezados ordenables; actualiza indicador visual
    - `bindPageSizeSelector()`: actualiza `pageSize` y vuelve a página 1 al cambiar el selector
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9_
  - [~] 11.3 Implementar `KPIManager`
    - `fetch(filters)`: llama `GET /api/orders/summary` con los filtros activos; llama `showSpinners()` antes de la llamada
    - `render(summary)`: actualiza cada tarjeta KPI con su valor formateado (total_revenue como `$X.XX`, avg_discount_pct como `X.X%`, cancellation_rate como `X.X%`, correlación con 3 decimales, top_brand y top_payment_method como texto, avg_shipping_cost_by_country como lista de 5 países)
    - `showSpinners()`: muestra el spinner en cada tarjeta KPI
    - `showError()`: muestra `"Error al cargar métricas. Intente nuevamente."` en el área del panel
    - Si la llamada tarda más de 5 s, mantener el spinner visible sin bloquear el resto de la UI
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  - [~] 11.4 Implementar `ChartManager` — gráficos estándar (bar, line, pie)
    - Definir `STATUS_COLORS = { Pending: '#F59E0B', Shipped: '#3B82F6', Delivered: '#10B981', Cancelled: '#EF4444', Returned: '#8B5CF6' }`
    - `fetch(filters)`: llama `GET /api/orders/charts`; llama `renderAll(payload)` al resolver
    - `destroyAndRecreate(id, config)`: destruye la instancia Chart.js existente antes de crear una nueva para evitar memory leaks
    - `renderBar(data)`: gráfico de barras con Chart.js; eje X = Country, eje Y = SUM(TotalAmount); tooltip con nombre, valor y porcentaje
    - `renderLine(data)`: gráfico de líneas; eje X = semanas ISO, eje Y = COUNT(OrderID)
    - `renderPie(data)`: gráfico de torta/donut; sectores por OrderStatus usando `STATUS_COLORS`; etiquetas de porcentaje; tooltip con nombre, valor y porcentaje
    - Si `data` está vacío, mostrar `"Sin datos para mostrar con los filtros actuales."` en el contenedor
    - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  - [~] 11.5 Implementar `ChartManager` — gráficos avanzados (heatmap, sankey, bubble, treemap)
    - `renderHeatmap(data)`: renderizar con Plotly.js tipo `heatmap`; celdas con valor 0 en el color más claro; tooltip con Country, Category y COUNT
    - `renderSankey(data)`: renderizar con Plotly.js tipo `sankey`; ancho de flujo proporcional a COUNT; tooltip con origen, destino y COUNT; aplicar `STATUS_COLORS` a los nodos de OrderStatus
    - `renderBubble(data)`: renderizar con Chart.js tipo `bubble`; eje X = avg_quantity, eje Y = avg_total_amount, tamaño = bubble_size (ya normalizado a [10,60]); etiquetar cada burbuja con el nombre de la categoría; tooltip con Category, AVG(Quantity), AVG(TotalAmount), AVG(ShippingCost)
    - `renderTreemap(data)`: renderizar con Plotly.js tipo `treemap`; nivel raíz = Category, nivel hoja = Brand; tamaño = SUM(TotalAmount); tooltip con Category, Brand y SUM(TotalAmount) en USD
    - Si `data` está vacío, mostrar `"Sin datos para mostrar con los filtros actuales."` en el contenedor correspondiente
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
  - [~] 11.6 Implementar `ExportManager` y el flujo de actualización paralela
    - `ExportManager.bindExportButton()`: escucha clic en `#btn-export`
    - `ExportManager.triggerDownload(filters)`: construye la URL `/api/orders/export` con los filtros activos y asigna a `window.location.href` para iniciar la descarga sin recargar la página
    - En `FilterManager.bindFormEvents()`, al aplicar filtros lanzar las 3 llamadas en paralelo con `Promise.all([TableManager.fetch(f), KPIManager.fetch(f), ChartManager.fetch(f)])`; cada manager muestra su propio spinner mientras espera
    - Al inicializar la página (`DOMContentLoaded`), llamar `FilterManager.bindFormEvents()`, `TableManager.bindSortHeaders()`, `TableManager.bindPageSizeSelector()`, `ExportManager.bindExportButton()` y disparar la carga inicial con filtros vacíos
    - _Requisitos: 2.3, 2.4, 4.8, 5.2, 6.5, 8.5_

- [~] 12. Implementar `static/css/dashboard.css` — estilos responsivos
  - Definir el layout base: panel de filtros en la parte superior, KPI panel debajo, sección de gráficos, tabla al final
  - Implementar breakpoint `@media (min-width: 1024px)`: gráficos en grid de 2 columnas
  - Implementar breakpoint `@media (min-width: 1280px)`: gráficos en grid de 3 columnas, KPI panel en fila horizontal
  - Implementar breakpoint `@media (min-width: 1920px)`: gráficos en grid de 4 columnas, tabla a ancho completo
  - Estilizar las tarjetas KPI con spinner visible durante la carga
  - Estilizar la tabla con encabezados ordenables (cursor pointer, indicador de dirección)
  - Estilizar los mensajes de error y de sin datos dentro de cada sección
  - _Requisitos: 2.5, 4.5, 5.3, 6.6_

- [~] 13. Punto de control final — verificar integración completa
  - Asegurarse de que todos los archivos del proyecto están creados según la estructura definida
  - Verificar que el dashboard carga en el navegador, los filtros funcionan, la tabla pagina correctamente, los KPIs se actualizan y los 7 gráficos se renderizan
  - Verificar que el botón de exportación descarga el CSV con las columnas correctas
  - Verificar que variables de entorno faltantes causan `sys.exit(1)` con el mensaje correcto
  - Preguntar al usuario si hay dudas antes de dar por finalizada la implementación.

---

## Notas

- El orden de las tareas respeta las dependencias: `config.py` → `db/connector.py` → `filters/engine.py` → `charts/renderer.py` → `api/` → `app.py` → frontend
- Cada tarea referencia los requisitos específicos para trazabilidad completa
- Los puntos de control (tareas 9 y 13) son momentos de validación incremental antes de continuar
- Toda la configuración sensible proviene exclusivamente de variables de entorno; nunca hardcodeada
- Todas las consultas SQL usan `%s` parametrizado; ninguna usa f-strings ni `.format()` en SQL
- En producción (`FLASK_ENV=production`), Flask debug está deshabilitado y los stack traces no se exponen en respuestas HTTP

---

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["2.1"] },
    { "id": 1, "tasks": ["3.1", "3.2"] },
    { "id": 2, "tasks": ["3.3", "3.4"] },
    { "id": 3, "tasks": ["4.1"] },
    { "id": 4, "tasks": ["4.2"] },
    { "id": 5, "tasks": ["5.1"] },
    { "id": 6, "tasks": ["5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "5.8"] },
    { "id": 7, "tasks": ["6.1", "6.2", "6.3", "7.1"] },
    { "id": 8, "tasks": ["10.1", "10.2", "10.3"] },
    { "id": 9, "tasks": ["11.1", "11.2", "11.3"] },
    { "id": 10, "tasks": ["11.4", "11.5"] },
    { "id": 11, "tasks": ["11.6"] }
  ]
}
```
