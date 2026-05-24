# Documento de Requisitos

## Introducción

SwiftShip Logistics Dashboard es una aplicación web construida con Flask y Python que se conecta a una base de datos PostgreSQL llamada "amazon". La aplicación permite a los analistas de operaciones de SwiftShip explorar, filtrar y visualizar datos de pedidos logísticos internacionales mediante gráficos avanzados e interactivos y una tabla de datos paginada. El objetivo es proporcionar visibilidad operativa sobre el rendimiento de envíos, tasas de cancelación, ingresos por categoría y marca, costos de envío por país, y patrones de comportamiento de pedidos a partir del conjunto de datos real con las columnas: `OrderID`, `OrderDate`, `CustomerID`, `CustomerName`, `ProductID`, `ProductName`, `Category`, `Brand`, `Quantity`, `UnitPrice`, `Discount`, `Tax`, `ShippingCost`, `TotalAmount`, `PaymentMethod`, `OrderStatus`, `City`, `State`, `Country`, `SellerID`.

## Glosario

- **Dashboard**: Interfaz web principal que muestra métricas, gráficos y la tabla de pedidos logísticos de SwiftShip.
- **Order**: Registro de un pedido logístico almacenado en la tabla principal de la base de datos PostgreSQL "amazon", identificado de forma única por `OrderID`.
- **Filter**: Mecanismo que permite al usuario acotar los datos mostrados según criterios basados en columnas reales del dataset.
- **Chart**: Representación gráfica de datos de pedidos generada a partir de datos agregados del dataset.
- **DB_Connector**: Componente responsable de establecer y gestionar el pool de conexiones con la base de datos PostgreSQL "amazon".
- **Filter_Engine**: Componente que valida y aplica los filtros seleccionados por el usuario construyendo cláusulas SQL parametrizadas.
- **Chart_Renderer**: Componente que agrega datos del dataset y genera los payloads JSON listos para renderizar en el frontend.
- **API_Layer**: Capa de endpoints Flask (Blueprints) que expone datos y operaciones al frontend en formato JSON.
- **Data_Table**: Componente de la interfaz que muestra los pedidos en formato tabular paginado y ordenable.
- **KPI_Panel**: Panel de indicadores clave de rendimiento que resume métricas agregadas calculadas sobre el dataset real.
- **Heatmap**: Gráfico de mapa de calor que representa la intensidad de un valor numérico en la intersección de dos dimensiones categóricas.
- **Sankey_Diagram**: Diagrama de flujo que muestra la distribución de pedidos a través de múltiples etapas categóricas.
- **Bubble_Chart**: Gráfico de burbujas donde cada burbuja representa un grupo de pedidos con tres dimensiones numéricas codificadas en posición X, posición Y y tamaño.
- **Treemap**: Gráfico de mapa de árbol que representa jerarquías de datos mediante rectángulos anidados proporcionales a un valor numérico.
- **OrderStatus**: Estado de un pedido; los valores válidos son exactamente: `'Pending'`, `'Shipped'`, `'Delivered'`, `'Cancelled'`, `'Returned'`.
- **TotalAmount**: Monto total de un pedido calculado como `(Quantity × UnitPrice × (1 - Discount)) + Tax + ShippingCost`.
- **CancellationRate**: Tasa de cancelación de una categoría, calculada como `COUNT(OrderID WHERE OrderStatus = 'Cancelled') / COUNT(OrderID)` para esa categoría.

---

## Requirements

### Requirement 1: Conexión a la Base de Datos PostgreSQL

**User Story:** Como analista de operaciones de SwiftShip, quiero que la aplicación se conecte de forma confiable a la base de datos PostgreSQL "amazon", para poder acceder a los datos actualizados de pedidos logísticos.

#### Acceptance Criteria

1. THE DB_Connector SHALL establecer una conexión con la base de datos PostgreSQL de nombre `amazon` utilizando los parámetros `DB_HOST`, `DB_PORT`, `DB_USER` y `DB_PASSWORD` cargados exclusivamente desde variables de entorno; IF alguna de estas variables de entorno está ausente al iniciar la aplicación, THEN THE DB_Connector SHALL registrar un mensaje de error que indique el nombre exacto de la variable faltante y SHALL terminar el proceso con código de salida no-cero.
2. THE DB_Connector SHALL mantener un pool de conexiones con un mínimo de 2 y un máximo de 10 conexiones concurrentes usando psycopg2.
3. WHEN el DB_Connector no logra establecer conexión con la base de datos, THE DB_Connector SHALL retornar un mensaje de error que incluya el tipo de excepción psycopg2 y el host/puerto intentados, y SHALL NOT incluir el valor de `DB_PASSWORD` en ningún mensaje de error o log.
4. WHEN una conexión del pool ha estado inactiva por más de 300 segundos y se intenta usar, THE DB_Connector SHALL reestablecer esa conexión antes de ejecutar la consulta; IF el reestablecimiento falla, THEN THE DB_Connector SHALL retornar un error de conexión al componente invocador y SHALL NOT lanzar una excepción no controlada.
5. IF una consulta SQL supera 30 segundos de tiempo de ejecución, THEN THE DB_Connector SHALL cancelar la consulta mediante `statement_timeout` de PostgreSQL y retornar un error de timeout con el mensaje `"Query timeout after 30 seconds"` al componente que la invocó.
6. THE DB_Connector SHALL ejecutar todas las consultas usando marcadores de posición parametrizados (`%s`) y SHALL NOT construir consultas SQL mediante concatenación de strings o f-strings.
7. WHEN todas las conexiones del pool están en uso y se solicita una nueva conexión, THE DB_Connector SHALL esperar hasta 5 segundos; IF no se libera ninguna conexión en ese tiempo, THEN THE DB_Connector SHALL retornar un error de pool exhausto con el mensaje `"Connection pool exhausted"` y SHALL NOT bloquear indefinidamente.

**Propiedades de corrección:**

- PARA TODO par de parámetros de conexión válidos `(host, port, user, password)`, THE DB_Connector SHALL retornar una conexión activa o un error descriptivo, nunca un estado indefinido.
- PARA TODA consulta parametrizada `q` con parámetros `p`, ejecutar `q` con `p` dos veces consecutivas sobre los mismos datos SHALL producir resultados idénticos (idempotencia de lectura).

---

### Requirement 2: Panel de KPIs Logísticos

**User Story:** Como analista de operaciones de SwiftShip, quiero ver un panel con métricas clave calculadas sobre los datos reales del dataset, para evaluar rápidamente el rendimiento operativo de los envíos.

#### Acceptance Criteria

1. THE KPI_Panel SHALL mostrar las siguientes métricas calculadas sobre el conjunto de pedidos actualmente filtrado:
   - **Total de ingresos**: `SUM(TotalAmount)` expresado en USD con dos decimales.
   - **Costo de envío promedio por país**: `AVG(ShippingCost) GROUP BY Country`, mostrando los 5 países con mayor costo promedio, cada uno con su valor en USD con dos decimales.
   - **Tasa de cancelación por categoría**: `COUNT(OrderID WHERE OrderStatus = 'Cancelled') / COUNT(OrderID) GROUP BY Category`, expresada como proporción en el rango `[0.0, 1.0]` con cuatro decimales, mostrada al usuario como porcentaje con un decimal.
   - **Descuento promedio**: `AVG(Discount) * 100` expresado como porcentaje en el rango `[0.0, 100.0]` con un decimal.
   - **Marca más vendida**: `Brand` con mayor `SUM(Quantity)` en el conjunto filtrado; en caso de empate, se retorna la marca con menor orden alfabético.
   - **Método de pago más utilizado**: `PaymentMethod` con mayor `COUNT(OrderID)` en el conjunto filtrado; en caso de empate, se retorna el método con menor orden alfabético.
   - **Correlación Descuento–Cancelación**: valor numérico de correlación estadística entre `Discount` y una variable binaria `is_cancelled` (1 si `OrderStatus = 'Cancelled'`, 0 en caso contrario), expresado con tres decimales en el rango `[-1.000, 1.000]`.
2. WHEN el conjunto de pedidos filtrado contiene cero registros, THE KPI_Panel SHALL mostrar `$0.00` para métricas monetarias, `N/A` para métricas de texto (marca, método de pago) y `0.0%` para métricas de porcentaje, y SHALL NOT mostrar un error de división por cero.
3. WHEN un usuario aplica o modifica filtros, THE KPI_Panel SHALL actualizar todas las métricas para reflejar el subconjunto filtrado en un plazo máximo de 2 segundos desde la aplicación del filtro, sin recargar la página completa.
4. THE KPI_Panel SHALL obtener sus datos desde el endpoint `/api/orders/summary` mediante una llamada `fetch()` asíncrona.
5. WHEN el endpoint `/api/orders/summary` tarda más de 5 segundos en responder, THE KPI_Panel SHALL mostrar un indicador de carga (spinner) visible en cada tarjeta de métrica y SHALL NOT bloquear la interacción del usuario con el resto del Dashboard.
6. WHEN la llamada `fetch()` al endpoint `/api/orders/summary` retorna un error HTTP (4xx o 5xx), THE KPI_Panel SHALL mostrar el mensaje `"Error al cargar métricas. Intente nuevamente."` en el área del panel y SHALL NOT mostrar valores parciales o incorrectos.

**Propiedades de corrección:**

- PARA TODO subconjunto filtrado `F` de pedidos, `SUM(TotalAmount)` calculado por el KPI_Panel SHALL ser igual a la suma aritmética de los valores `TotalAmount` de todos los registros en `F`.
- PARA TODA categoría `C` con al menos un pedido, la `CancellationRate` de `C` SHALL estar en el rango `[0.0, 1.0]`.
- PARA TODO conjunto filtrado `F`, la marca más vendida retornada SHALL tener `SUM(Quantity)` mayor o igual al `SUM(Quantity)` de cualquier otra marca en `F`.

---

### Requirement 3: Filtrado de Pedidos por Columnas Reales

**User Story:** Como analista de operaciones de SwiftShip, quiero filtrar los pedidos logísticos usando los campos reales del dataset, para enfocar mi análisis en subconjuntos específicos de datos.

#### Acceptance Criteria

1. THE Filter_Engine SHALL soportar los siguientes parámetros de filtro, todos opcionales y combinables con lógica AND:
   - `date_from` y `date_to`: rango de fechas aplicado sobre la columna `OrderDate` (formato `YYYY-MM-DD`, ambos extremos inclusivos).
   - `status`: valor único o lista de valores de `OrderStatus`; valores válidos: `'Pending'`, `'Shipped'`, `'Delivered'`, `'Cancelled'`, `'Returned'`.
   - `country`: valor único o lista de valores de `Country`.
   - `category`: valor único o lista de valores de `Category`.
   - `brand`: valor único o lista de valores de `Brand`.
   - `payment_method`: valor único o lista de valores de `PaymentMethod`.
   - `seller_id`: valor único o lista de valores de `SellerID`.
2. WHEN un usuario aplica uno o más filtros, THE Filter_Engine SHALL retornar únicamente los pedidos que satisfacen simultáneamente todos los criterios seleccionados (lógica AND), con un máximo de 1000 registros ordenados por `OrderDate` descendente.
3. WHEN el parámetro `date_from` es posterior a `date_to`, THE Filter_Engine SHALL retornar un error HTTP 400 con el mensaje `"date_from must be earlier than or equal to date_to"` y SHALL NOT ejecutar ninguna consulta a la base de datos.
4. WHEN el parámetro `status` contiene un valor que no pertenece al conjunto `{'Pending', 'Shipped', 'Delivered', 'Cancelled', 'Returned'}`, THE Filter_Engine SHALL retornar un error HTTP 400 con el mensaje `"Invalid status value: <valor>"`.
5. WHEN ningún filtro es aplicado, THE Filter_Engine SHALL retornar hasta 1000 registros ordenados por `OrderDate` descendente.
6. THE Filter_Engine SHALL construir todas las cláusulas WHERE usando marcadores de posición parametrizados (`%s`) y SHALL NOT interpolar valores de filtro directamente en el string SQL.
7. WHEN se aplica un filtro de lista (por ejemplo, múltiples `country`), THE Filter_Engine SHALL usar una cláusula `IN` parametrizada y SHALL retornar pedidos que coincidan con cualquiera de los valores de la lista.
8. IF el parámetro `date_from` o `date_to` no tiene el formato `YYYY-MM-DD` (por ejemplo, `32-13-2024` o `2024/01/15`), THEN THE Filter_Engine SHALL retornar HTTP 400 con el mensaje `"Invalid date format. Expected YYYY-MM-DD"` y SHALL NOT ejecutar ninguna consulta a la base de datos.
9. WHEN un conjunto de filtros válidos no produce ningún resultado, THE Filter_Engine SHALL retornar HTTP 200 con un array JSON vacío `[]` y SHALL NOT retornar un error.

**Propiedades de corrección:**

- PARA TODO conjunto de filtros válidos `F`, el conjunto de pedidos retornado `R` SHALL satisfacer: para todo pedido `o` en `R`, `o` cumple todos los criterios de `F`.
- PARA TODO conjunto de filtros válidos `F`, ningún pedido que no cumpla algún criterio de `F` SHALL aparecer en `R` (completitud y precisión del filtrado).
- PARA TODO filtro de rango de fechas `[d1, d2]`, todos los pedidos en `R` SHALL tener `OrderDate >= d1` AND `OrderDate <= d2`.
- Aplicar el mismo conjunto de filtros `F` dos veces consecutivas sobre los mismos datos SHALL producir el mismo conjunto de resultados `R` (idempotencia).

---

### Requirement 4: Tabla de Datos de Pedidos

**User Story:** Como analista de operaciones de SwiftShip, quiero explorar los pedidos en una tabla paginada con las columnas reales del dataset, para inspeccionar el detalle de cada pedido de forma eficiente.

#### Acceptance Criteria

1. THE Data_Table SHALL mostrar los pedidos en formato tabular con exactamente las siguientes columnas en este orden: `OrderID`, `OrderDate`, `CustomerName`, `ProductName`, `Category`, `Brand`, `Quantity`, `UnitPrice`, `Discount`, `Tax`, `ShippingCost`, `TotalAmount`, `PaymentMethod`, `OrderStatus`, `City`, `State`, `Country`.
2. THE Data_Table SHALL soportar paginación con tamaños de página configurables de 10, 25 o 50 filas por página, con un valor por defecto de 25.
3. WHEN un usuario selecciona un tamaño de página `n` y navega a la página número `p`, THE Data_Table SHALL mostrar exactamente las filas desde el índice `(p-1)*n` hasta `min(p*n - 1, total-1)` del conjunto de pedidos filtrado y ordenado.
4. WHEN un usuario hace clic en el encabezado de una columna ordenable (`OrderDate`, `TotalAmount`, `ShippingCost`, `Quantity`, `Discount`), THE Data_Table SHALL ordenar los datos en orden ascendente en el primer clic, en orden descendente en el segundo clic, y volver a ascendente en el tercer clic; el estado de ordenamiento por defecto SHALL ser `OrderDate` descendente.
5. WHEN el conjunto de pedidos filtrado contiene cero registros, THE Data_Table SHALL mostrar el mensaje `"No se encontraron pedidos con los filtros seleccionados."` en el área de la tabla y SHALL NOT mostrar filas vacías.
6. THE Data_Table SHALL mostrar el conteo total de pedidos filtrados en el formato `"Mostrando X–Y de Z pedidos"` encima de la tabla.
7. THE Data_Table SHALL formatear la columna `Discount` como porcentaje con un decimal (ej. `15.0%`), la columna `UnitPrice`, `ShippingCost`, `Tax` y `TotalAmount` como valores monetarios en USD con dos decimales (ej. `$123.45`).
8. WHEN un usuario cambia los filtros, el ordenamiento o la página activa, THE Data_Table SHALL realizar una llamada `fetch()` asíncrona al endpoint `/api/orders` con los parámetros actualizados, actualizar su contenido sin recargar la página completa, y restablecer la paginación a la página 1 cuando cambien los filtros o el ordenamiento.
9. WHEN la llamada `fetch()` al endpoint `/api/orders` retorna un error HTTP (4xx o 5xx), THE Data_Table SHALL mostrar el mensaje `"Error al cargar los datos. Intente nuevamente."` en el área de la tabla y SHALL NOT mostrar datos parciales o de una solicitud anterior.

**Propiedades de corrección:**

- PARA TODO conjunto filtrado de `Z` pedidos y tamaño de página `n`, el número total de páginas SHALL ser `ceil(Z / n)`.
- PARA TODA página `p` con `n` filas, la unión de todas las páginas SHALL contener exactamente los mismos `Z` pedidos sin duplicados ni omisiones.
- PARA TODO ordenamiento por columna `C` en dirección `D`, los valores de `C` en las filas mostradas SHALL estar ordenados según `D` (ascendente o descendente).

---

### Requirement 5: Gráficos Estándar

**User Story:** Como analista de operaciones de SwiftShip, quiero ver gráficos estándar que reflejen las columnas reales del dataset y se actualicen con los filtros aplicados, para identificar tendencias y distribuciones en los datos logísticos.

#### Acceptance Criteria

1. THE Chart_Renderer SHALL generar los siguientes gráficos estándar a partir de los datos filtrados:
   - **Gráfico de barras — TotalAmount por Country**: eje X = `Country`, eje Y = `SUM(TotalAmount)`, ordenado de mayor a menor, mostrando los 15 países con mayor ingreso total.
   - **Gráfico de líneas — Volumen de pedidos por OrderDate**: eje X = `OrderDate` agregado por semana (inicio de semana ISO), eje Y = `COUNT(OrderID)`, mostrando la tendencia temporal completa del conjunto filtrado.
   - **Gráfico de torta/donut — Distribución de OrderStatus**: sectores proporcionales a `COUNT(OrderID)` para cada valor de `OrderStatus` (`Pending`, `Shipped`, `Delivered`, `Cancelled`, `Returned`), con etiquetas de porcentaje.
2. WHEN un usuario aplica o modifica filtros, THE Chart_Renderer SHALL recalcular y actualizar los tres gráficos estándar para reflejar el subconjunto filtrado sin recargar la página completa.
3. WHEN un gráfico contiene cero puntos de datos tras el filtrado, THE Chart_Renderer SHALL mostrar el mensaje `"Sin datos para mostrar con los filtros actuales."` dentro del área del gráfico.
4. THE Chart_Renderer SHALL mostrar tooltips con valores exactos al pasar el cursor sobre un punto de datos, barra o sector: para barras y torta, el tooltip SHALL incluir el nombre de la categoría, el valor numérico y el porcentaje sobre el total.
5. THE Chart_Renderer SHALL usar una paleta de colores consistente donde cada valor de `OrderStatus` tenga siempre el mismo color en todos los gráficos del Dashboard.
6. THE Chart_Renderer SHALL renderizar los gráficos usando Chart.js o Plotly.js servido desde la aplicación Flask.

**Propiedades de corrección:**

- PARA TODO gráfico de torta de `OrderStatus`, la suma de los porcentajes de todos los sectores SHALL ser igual a 100% (con tolerancia de ±0.1% por redondeo).
- PARA TODO gráfico de barras de `TotalAmount por Country`, el valor de cada barra SHALL ser igual a `SUM(TotalAmount)` de los pedidos del conjunto filtrado para ese `Country`.
- PARA TODO gráfico de líneas, el número de puntos en el eje X SHALL ser igual al número de semanas distintas presentes en el conjunto filtrado.

---

### Requirement 6: Gráficos Avanzados

**User Story:** Como analista de operaciones de SwiftShip, quiero ver gráficos avanzados que revelen patrones multidimensionales en los datos logísticos, para obtener insights que los gráficos estándar no pueden mostrar.

#### Acceptance Criteria

1. THE Chart_Renderer SHALL generar un **Heatmap de pedidos por Country vs Category**:
   - Eje X: valores únicos de `Category`.
   - Eje Y: valores únicos de `Country`.
   - Valor de cada celda: `COUNT(OrderID)` para la combinación `(Country, Category)` en el conjunto filtrado.
   - Celdas con valor 0 SHALL mostrarse en el color más claro de la escala de color.
   - El tooltip de cada celda SHALL mostrar: `Country`, `Category` y `COUNT(OrderID)`.

2. THE Chart_Renderer SHALL generar un **Sankey Diagram de flujo de pedidos Country → Category → OrderStatus**:
   - Nodos de nivel 1: valores únicos de `Country` (los 10 países con mayor `COUNT(OrderID)`).
   - Nodos de nivel 2: valores únicos de `Category`.
   - Nodos de nivel 3: valores únicos de `OrderStatus`.
   - El ancho de cada flujo SHALL ser proporcional a `COUNT(OrderID)` para esa combinación de nodos.
   - El tooltip de cada flujo SHALL mostrar el origen, el destino y el `COUNT(OrderID)`.

3. THE Chart_Renderer SHALL generar un **Bubble Chart de Quantity vs TotalAmount vs ShippingCost**:
   - Eje X: `AVG(Quantity)` agrupado por `Category`.
   - Eje Y: `AVG(TotalAmount)` agrupado por `Category`.
   - Tamaño de burbuja: `AVG(ShippingCost)` agrupado por `Category`, normalizado al rango de píxeles `[10, 60]`.
   - Cada burbuja representa una `Category` distinta y SHALL estar etiquetada con el nombre de la categoría.
   - El tooltip SHALL mostrar: `Category`, `AVG(Quantity)`, `AVG(TotalAmount)` y `AVG(ShippingCost)`.

4. THE Chart_Renderer SHALL generar un **Treemap de ingresos por Category → Brand**:
   - Nivel raíz: `Category`.
   - Nivel hoja: `Brand` dentro de cada `Category`.
   - Tamaño de cada rectángulo hoja: `SUM(TotalAmount)` para esa combinación `(Category, Brand)` en el conjunto filtrado.
   - El tooltip de cada rectángulo SHALL mostrar: `Category`, `Brand` y `SUM(TotalAmount)` en USD.

5. WHEN un usuario aplica o modifica filtros, THE Chart_Renderer SHALL recalcular y actualizar los cuatro gráficos avanzados para reflejar el subconjunto filtrado sin recargar la página completa.
6. WHEN cualquier gráfico avanzado contiene cero combinaciones de datos tras el filtrado, THE Chart_Renderer SHALL mostrar el mensaje `"Sin datos para mostrar con los filtros actuales."` dentro del área del gráfico correspondiente.
7. THE Chart_Renderer SHALL obtener los datos para los gráficos avanzados desde el endpoint `/api/orders/charts` mediante llamadas `fetch()` asíncronas.

**Propiedades de corrección:**

- PARA TODO Heatmap generado, la suma de todos los valores de celda SHALL ser igual a `COUNT(OrderID)` total del conjunto filtrado.
- PARA TODO Sankey Diagram generado, la suma de los flujos que entran a cada nodo de nivel 2 SHALL ser igual a la suma de los flujos que salen de ese nodo hacia el nivel 3.
- PARA TODO Treemap generado, la suma de `SUM(TotalAmount)` de todos los rectángulos hoja SHALL ser igual a `SUM(TotalAmount)` total del conjunto filtrado.
- PARA TODO Bubble Chart generado, el número de burbujas SHALL ser igual al número de valores únicos de `Category` presentes en el conjunto filtrado.

---

### Requirement 7: API de Datos (Endpoints Flask)

**User Story:** Como desarrollador frontend de SwiftShip, quiero un conjunto de endpoints Flask que retornen datos logísticos en formato JSON usando los parámetros de filtro reales del dataset, para que el frontend pueda obtener y mostrar datos dinámicamente.

#### Acceptance Criteria

1. THE API_Layer SHALL exponer un endpoint `GET /api/orders` que acepte los siguientes parámetros de query opcionales: `date_from` (YYYY-MM-DD), `date_to` (YYYY-MM-DD), `status` (uno o varios), `country` (uno o varios), `category` (uno o varios), `brand` (uno o varios), `payment_method` (uno o varios), `seller_id` (uno o varios); y retorne un array JSON de pedidos con los campos: `OrderID`, `OrderDate`, `CustomerName`, `ProductName`, `Category`, `Brand`, `Quantity`, `UnitPrice`, `Discount`, `Tax`, `ShippingCost`, `TotalAmount`, `PaymentMethod`, `OrderStatus`, `City`, `State`, `Country`.

2. THE API_Layer SHALL exponer un endpoint `GET /api/orders/summary` que acepte los mismos parámetros de filtro que `/api/orders` y retorne un objeto JSON con exactamente las siguientes claves:
   ```json
   {
     "total_revenue": <float, 2 decimales>,
     "avg_shipping_cost_by_country": [{"country": <str>, "avg_shipping_cost": <float>}, ...],
     "cancellation_rate_by_category": [{"category": <str>, "cancellation_rate": <float>}, ...],
     "avg_discount_pct": <float, 1 decimal>,
     "top_brand_by_quantity": <str>,
     "top_payment_method": <str>,
     "discount_cancellation_correlation": <float, 3 decimales>
   }
   ```

3. THE API_Layer SHALL exponer un endpoint `GET /api/orders/charts` que acepte los mismos parámetros de filtro y retorne un objeto JSON con las claves: `bar_total_amount_by_country`, `line_orders_by_week`, `pie_order_status`, `heatmap_country_category`, `sankey_country_category_status`, `bubble_category_metrics`, `treemap_category_brand`.

4. THE API_Layer SHALL exponer un endpoint `GET /api/orders/export` que acepte los mismos parámetros de filtro y retorne un archivo CSV descargable con las columnas: `OrderID`, `OrderDate`, `CustomerID`, `CustomerName`, `ProductID`, `ProductName`, `Category`, `Brand`, `Quantity`, `UnitPrice`, `Discount`, `Tax`, `ShippingCost`, `TotalAmount`, `PaymentMethod`, `OrderStatus`, `City`, `State`, `Country`, `SellerID`.

5. WHEN una solicitud a cualquier endpoint contiene un valor de parámetro inválido (por ejemplo, `status=InvalidValue` o `date_from=32-13-2024`), THE API_Layer SHALL retornar HTTP 400 con un cuerpo JSON `{"error": "<descripción específica del parámetro inválido>"}`.

6. WHEN ocurre un error interno durante el procesamiento de una solicitud, THE API_Layer SHALL retornar HTTP 500 con el cuerpo JSON `{"error": "Internal server error"}` y SHALL registrar el traceback completo en el log del servidor.

7. THE API_Layer SHALL incluir el header `Content-Type: application/json` en todas las respuestas JSON y el header `Content-Disposition: attachment; filename="swiftship_orders_export.csv"` en las respuestas del endpoint de exportación.

8. THE API_Layer SHALL limitar el endpoint `/api/orders/export` a un máximo de 10,000 filas por solicitud; WHEN el conjunto filtrado supera 10,000 registros, THE API_Layer SHALL retornar los primeros 10,000 ordenados por `OrderDate` descendente e incluir el header `X-Export-Truncated: true`.

9. THE API_Layer SHALL incluir headers CORS que permitan solicitudes únicamente desde el mismo origen.

**Propiedades de corrección:**

- PARA TODO conjunto de parámetros de filtro válidos `F`, el array retornado por `/api/orders` SHALL contener exactamente los mismos pedidos que retornaría el Filter_Engine con los mismos parámetros `F`.
- PARA TODO conjunto de filtros `F`, el campo `total_revenue` retornado por `/api/orders/summary` SHALL ser igual a `SUM(TotalAmount)` de todos los pedidos retornados por `/api/orders` con los mismos filtros `F`.
- PARA TODO conjunto de filtros `F`, el CSV retornado por `/api/orders/export` SHALL contener exactamente las mismas filas que `/api/orders` con los mismos filtros `F` (hasta el límite de 10,000 filas), con los mismos valores en cada campo (propiedad de round-trip: los datos del JSON y del CSV deben ser equivalentes).

---

### Requirement 8: Exportación de Datos a CSV

**User Story:** Como analista de operaciones de SwiftShip, quiero exportar los pedidos actualmente filtrados a un archivo CSV con todas las columnas del dataset, para realizar análisis adicionales en herramientas externas.

#### Acceptance Criteria

1. THE API_Layer SHALL generar el archivo CSV con una fila de encabezado que contenga exactamente los nombres de columna: `OrderID,OrderDate,CustomerID,CustomerName,ProductID,ProductName,Category,Brand,Quantity,UnitPrice,Discount,Tax,ShippingCost,TotalAmount,PaymentMethod,OrderStatus,City,State,Country,SellerID`.
2. WHEN el conjunto de pedidos filtrado contiene cero registros, THE API_Layer SHALL retornar un CSV que contenga únicamente la fila de encabezado y SHALL retornar HTTP 200 (no un error).
3. THE API_Layer SHALL limitar la exportación a un máximo de 10,000 filas; WHEN el conjunto filtrado supera este límite, THE API_Layer SHALL incluir el header `X-Export-Truncated: true` en la respuesta.
4. THE API_Layer SHALL formatear los valores de `Discount` en el CSV como decimales en el rango `[0, 1]` (por ejemplo, `0.15` para 15%) y los valores monetarios (`UnitPrice`, `ShippingCost`, `Tax`, `TotalAmount`) con dos decimales.
5. WHEN un usuario hace clic en el botón de exportación del Dashboard, THE Dashboard SHALL construir la URL de exportación incluyendo todos los parámetros de filtro actualmente aplicados y SHALL iniciar la descarga del archivo sin recargar la página.

**Propiedades de corrección:**

- PARA TODO archivo CSV exportado con `N` filas de datos, `N` SHALL ser menor o igual a 10,000.
- PARA TODO archivo CSV exportado, el número de columnas en cada fila de datos SHALL ser igual al número de columnas en la fila de encabezado (20 columnas).
- PARA TODO conjunto de filtros `F` que produzca `N ≤ 10,000` pedidos, el CSV exportado SHALL contener exactamente `N` filas de datos (sin duplicados ni omisiones).

---

### Requirement 9: Seguridad y Configuración

**User Story:** Como administrador de sistemas de SwiftShip, quiero que la aplicación siga prácticas seguras de configuración y manejo de datos, para que las credenciales y datos sensibles no queden expuestos.

#### Acceptance Criteria

1. THE Dashboard SHALL cargar todos los valores de configuración sensibles (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `FLASK_SECRET_KEY`) exclusivamente desde variables de entorno y SHALL NOT incluir estos valores en el código fuente ni en archivos de configuración versionados.
2. IF alguna variable de entorno requerida para la conexión a la base de datos está ausente al iniciar la aplicación, THEN THE Dashboard SHALL registrar un mensaje de error descriptivo que indique el nombre de la variable faltante y SHALL terminar el proceso de inicio con código de salida no-cero.
3. THE API_Layer SHALL sanitizar todos los parámetros de entrada del usuario antes de pasarlos al Filter_Engine, rechazando cualquier valor que contenga caracteres de control SQL (`'`, `"`, `;`, `--`, `/*`, `*/`).
4. WHILE la aplicación está ejecutándose en modo producción (`FLASK_ENV=production`), THE Dashboard SHALL deshabilitar el modo debug de Flask y SHALL NOT incluir stack traces en las respuestas HTTP.
5. THE API_Layer SHALL validar que los parámetros `date_from` y `date_to` sean fechas válidas en formato `YYYY-MM-DD` antes de construir cualquier consulta SQL; IF el formato es inválido, THEN THE API_Layer SHALL retornar HTTP 400 con el mensaje `"Invalid date format. Expected YYYY-MM-DD"`.
6. THE DB_Connector SHALL usar exclusivamente consultas parametrizadas con `%s` para todos los valores provenientes de parámetros de usuario, incluyendo listas de valores en cláusulas `IN`.
