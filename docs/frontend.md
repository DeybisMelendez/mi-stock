# Frontend

Documentación del frontend: stack, plantillas, filtros de template y
convenciones. Para la guía de CSS, ver [`docs/estilos.md`](estilos.md).

## Stack (todo por CDN, sin build)

| Tecnología | Versión | Carga | Propósito |
|---|---|---|---|
| [Pico CSS](https://picocss.com/) | 2.x (tema orange) | `templates/layout.html` | Base del estilo |
| Material Icons | última | `templates/layout.html` | Iconografía |
| [AlpineJS](https://alpinejs.dev/) | última | `templates/layout.html` | Reactividad ligera |
| [Grid.js](https://gridjs.io/) | última | `templates/layout.html` | Tablas con búsqueda y paginación |
| [Chart.js](https://www.chartjs.org/) | última | `templates/home.html` (solo aquí) | Gráficos del dashboard |

**No hay**:

- `package.json`.
- Node modules.
- Pipelines de build (`npm run dev`, `vite build`, etc.).
- Archivos en `static/` excepto `static/css/styles.css` (más la
  carpeta `media/` con fotos subidas).

Si necesitas agregar JS, hazlo inline en el template (como ya hacen
`home.html` e `invoice_form.html`).

## Estructura de `templates/`

```
templates/
├── layout.html              # Layout base: navbar, CDN, mensajes
├── includes/
│   ├── grid_table.html      # Parcial: tabla Grid.js parametrizable
│   ├── tag_filter.html      # Parcial: barra de filtro por etiqueta
│   ├── period_nav.html      # Parcial: navegación de períodos de reportes
│   └── messages.html        # Mensajes Django descartables
├── product_list.html        # Lista de productos (tabs + filtro etiqueta)
├── category_list.html       # Lista de categorías
├── tag_list.html            # Lista de etiquetas
├── customer_list.html       # Lista de clientes
├── expensecategory_list.html
├── otherincomecategory_list.html
├── expense_list.html        # Lista de gastos
├── otherincome_list.html    # Lista de otros ingresos
├── purchase_list.html       # Lista de facturas de compra
├── sale_list.html           # Lista de facturas de venta
├── category_form.html       # Form de categoría (patrón de los 7 forms simples)
├── tag_form.html            # (tag, customer, expensecategory,
├── customer_form.html       #  otherincomecategory, expense y
├── expensecategory_form.html    #  otherincome tienen su propio form)
├── otherincomecategory_form.html
├── expense_form.html
├── otherincome_form.html
├── product_form.html        # Producto + formset de fotos (con Alpine mínimo)
├── invoice_form.html        # Factura compra/venta + formset + Alpine para subtotales
├── product_detail.html      # Detalle de producto con galería
├── invoice_detail.html      # Detalle de factura (solo lectura)
├── home.html                # Dashboard: KPIs, gráficos, top productos, alertas
├── month_result.html        # Estado de resultados mensual
├── top_products.html        # Reporte: productos más vendidos
├── sales_by_department.html # Reporte: ventas por departamento
├── sales_by_tag.html        # Reporte: ventas por etiqueta
├── user_profile.html        # Perfil de usuario + logout
├── import_form.html         # Subida de archivo de respaldo
└── registration/
    └── login.html           # Login estándar
```

> **Convención**: cada modelo CRUD simple tiene su par
> `<m>_list.html` + `<m>_form.html` y cada vista su template propio.
> Lo mecánico (Grid.js, filtro de etiquetas, navegación de períodos)
> vive en parciales bajo `includes/` para no duplicar JS.

## Parciales reutilizables (`includes/`)

### `grid_table.html` — Tabla Grid.js

Monta una tabla Grid.js (búsqueda, paginación de 25, orden con iconos
Material, idioma español). Se incluye con `{% include ... with ... only %}`:

| Parámetro | Descripción |
|---|---|
| `container_id` | id único del `<div>` contenedor (una página puede tener varias tablas) |
| `headers_json` | JSON array con los encabezados |
| `data_json` | JSON array de filas (arrays de strings) |
| `no_actions` | pasar `True` para tablas de solo lectura (reportes) |
| `empty_message` | mensaje cuando no hay registros |

**Celda de acciones**: si la tabla tiene acciones (default), la última
celda de cada fila es un objeto (o string JSON) con las URLs a
renderizar como iconos:

```json
{"detail": "...", "edit": "..."}
```

El parcial renderiza `visibility` (ver) y `edit` (editar). Si además
hay `"toggle"` (lista de productos), renderiza un mini-form POST con
icono `toggle_on`/`toggle_off` (activar/desactivar), leyendo el token
CSRF de `<input id="csrf-token">` (que `product_list.html` añade) y
preservando `next`. La vista serializa estos objetos en Python; el
parcial solo los convierte en iconos.

### `tag_filter.html` — Barra de filtro por etiqueta

Incluida por `product_list.html`, `purchase_list.html` y
`sale_list.html`. Parámetros: `available_tags` (lista de `{id, name}`),
`selected_tag`, `clear_url` (URL del enlace "Limpiar filtro") y
`preserve_tab` (solo `product_list.html`, para mantener `?tab=` al
cambiar etiqueta). El `select` hace submit automático vía AlpineJS
(`@change="$event.target.form.submit()"`).

### `period_nav.html` — Navegación de períodos

Incluida por los tres templates de reportes (`top_products.html`,
`sales_by_department.html`, `sales_by_tag.html`). Parámetros:
`url_name` (nombre de URL que recibe `<str:period>`), `period`
(período actual, resaltado en negrita) y `periods` (lista de pares
`(clave, etiqueta)` alimentada por la constante `REPORT_PERIODS` de
`views.py`).

## Layout base (`layout.html`)

Carga los CDN de Pico, Material Icons, AlpineJS y Grid.js. Contiene
la barra de navegación única (misma en todas las pantallas):

- Si `user.is_authenticated`:
  - Botón hamburguesa (`.nav-toggle`) a la **izquierda**.
  - Enlace "Home" (que apunta a `home`) a la **derecha**.
  - Al pulsar la hamburguesa se abre un panel off-canvas
    (`<aside id="nav-panel">`) con backdrop, que contiene el menú
    completo agrupado en 5 secciones (Catálogo / Operaciones /
    Reportes / Cuenta / Datos).
- Si no: enlace "Iniciar sesión" a la derecha.

Debajo del `<nav>`:

```html
{% include "includes/messages.html" %}
{% block content %}{% endblock %}
```

Y al final del `<body>` se cargan los scripts de Alpine y Grid.js
más, si el usuario está autenticado, el JS mínimo que controla el
panel off-canvas (abrir/cerrar `#nav-panel`, `.nav-backdrop`, tecla
`Esc`).

### Diseño responsive / móvil

La app es **mobile-first** en su CSS. El breakpoint principal del
proyecto es **768 px**:

- **`< 768 px` (móvil/tablet vertical):**
  - El panel off-canvas cubre `80vw` (máx 320 px) desde la izquierda.
  - Las tablas (`month_result.html`, las listas, formset de facturas)
    hacen scroll horizontal dentro de `.table-wrap` con sombra lateral
    indicando "hay más →".
  - El formset de `invoice_form.html` se renderiza como **cards
    apiladas**: cada `<tr>` es una tarjeta con etiqueta (`data-label`)
    arriba y el campo abajo. El total general queda en una caja fija
    al final.
  - Botones y enlaces con `role="button"` garantizan `min-height: 44px`
    (regla WCAG 2.5.5 para tap targets).
- **`≥ 768 px` (escritorio):**
  - El panel ocupa `320px` desde la izquierda y se muestra
    superpuesto al contenido (con backdrop) en lugar de empujarlo.
  - Tablas se ven como tablas. Formset de facturas como tabla 5
    columnas. Sin cambios visuales respecto al comportamiento previo.

El navbar es único en todas las pantallas: hamburguesa a la izquierda
+ "Home" a la derecha. El menú completo solo vive en el panel
off-canvas.

> **Si añades un enlace al menú**, edita el `<ul class="nav-panel__list">`
> en `templates/layout.html`.
>
> Si añades una tabla nueva, envuélvela en `<div class="table-wrap">`
> para que herede el scroll horizontal optimizado en móvil.
>
> Si añades un formset con muchas columnas, pon `data-label` en cada
> `<td>` para que el CSS móvil pueda convertir la tabla en cards.

## Templates de lista

Todas las listas siguen el mismo esqueleto:

```html
{% extends "layout.html" %}
{% block content %}
<main class="container">
  <h1>{{ title }}</h1>
  <a href="{% url '<m>_new' %}" role="button"><i class="material-icons">add</i> Nuevo</a>
  <hr>
  {% include "includes/grid_table.html" with container_id="gridjs-table" headers_json=headers_json data_json=data_json only %}
</main>
{% endblock %}
```

La vista serializa las filas en Python (`headers_json` +
`data_json`), con la última celda como objeto de acciones
`{"edit": ...}` (ver `vistas-y-urls.md`). El template solo aporta el
título, el botón "Nuevo" y los parciales necesarios.

### `product_list.html` — Lista de productos

La más interactiva de las listas:

- AlpineJS (`x-data="productTabs(...)"`) controla los tabs
  activos/inactivos y actualiza `?tab=` en la URL.
- Incluye `grid_table.html` **dos veces** (`container_id` distintos:
  `gridjs-active` / `gridjs-inactive`), una por tab.
- Incluye `tag_filter.html` con `preserve_tab=True`.
- Añade `<input type="hidden" id="csrf-token">` para el mini-form
  POST de activar/desactivar del parcial.

### `purchase_list.html` / `sale_list.html` — Listas de facturas

Botón "Nueva" hacia `purchase_invoice_new` / `sale_invoice_new` +
`tag_filter.html` + `grid_table.html`. Main lleva `x-data="{}"` para
que AlpineJS procese el `@change` del filtro.

### Reportes (`top_products.html`, `sales_by_department.html`, `sales_by_tag.html`)

Título + `period_nav.html` + `grid_table.html` con `no_actions=True`
(sin columna de acciones).

## Templates de formulario

### `<m>_form.html` — Formularios de los modelos simples

Los 7 templates (`category_form.html`, `tag_form.html`,
`customer_form.html`, `expensecategory_form.html`,
`otherincomecategory_form.html`, `expense_form.html`,
`otherincome_form.html`) comparten el mismo esqueleto:

```html
<form method="post">
    {% csrf_token %}
    {{ form.as_div }}
    <button type="submit">Guardar</button>
</form>
```

No tienen JS. Cada uno existe por separado para que pueda evolucionar
independiente (campos, widgets, validación en cliente, etc.).

Tras guardar, la vista `<m>_form_view` redirige a:

- La **lista** del modelo si venía de una edición (`pk` presente).
- Un **formulario vacío** si venía de una creación (`pk` ausente),
  para permitir el flujo batch de "crear varios seguidos".

### `product_form.html` — Producto + fotos

- Form principal `ProductForm` (campos del producto).
- Formset `ProductImageFormSet` para múltiples fotos.
- Botón "+ Agregar foto" usa un pequeño JS inline (`addItemRow()`) que
  clona una fila de la plantilla oculta `#empty-row-template` y
  incrementa `TOTAL_FORMS`.
- Muestra thumbnails de fotos existentes en el formset de edición.

Tras guardar, `product_form_view` redirige a:

- `product_detail` del producto recién guardado si venía de una
  edición (`pk` presente), para mostrar el resultado de los cambios.
- `product_new` (formulario vacío) si venía de una creación.

### `invoice_form.html` — Factura + líneas (AlpineJS)

La más interactiva. Renderiza:

- Cabecera de la factura (`PurchaseInvoiceForm` o `SaleInvoiceForm`).
- **Enlace a cliente nuevo** (solo ventas): bloque discreto con un
  enlace "Registrar nuevo cliente" que abre el CRUD en pestaña nueva.
  El selector `customer_obj` se renderiza dentro de `{{ form.as_div }}`
  por ser un campo normal del modelo. No hay campo de texto libre:
  el cliente debe estar registrado (la migración `0013` consolidó
  la FK como única vía).
- Tabla de líneas con el formset inline.
- AlpineJS calcula subtotales por línea y total general en vivo,
  leyendo:
  - `product_prices_json` — `{product_id: price}`
  - `product_costs_json` — `{product_id: average_cost}` (solo compras)
  - `product_stocks_json` — `{product_id: stock}` (para hint en ventas)

El botón "+ Agregar línea" clona una fila de `#empty-row-source`,
reemplaza el `__FORMKEY__` por el nuevo índice y actualiza
`TOTAL_FORMS`.

> Si añades un campo nuevo al `Purchase`/`Sale`, **debes actualizar
> también `invoice_form.html`** para que se muestre en la tabla.

## `product_detail.html` — Detalle de producto

Galería de fotos con AlpineJS (`x-data="{ active: ... }"`):

- Imagen principal que cambia al hacer clic en una miniatura.
- Tabla de archivos descargables (botón `download` en cada fila).
- Tarjetas de información: general, inventario, precio/margen,
  historial (ventas y compras).
- Si `unit_margin < 0`, muestra badge de advertencia "Precio por
  debajo del costo".
- Si `product.active` es `False`, muestra badge "Inactivo".

## `invoice_detail.html` — Detalle de factura

Solo lectura. Cabecera (cliente/proveedor + fecha) + tabla de líneas +
total. Botones para volver a la lista y editar.

## `home.html` — Dashboard

Carga Chart.js (solo esta página). Calcula y muestra:

- 4 KPIs (cards): Ventas del Mes, Valor de Inventario, Ganancia Neta
  del Mes, Gastos del Mes.
- Tendencias (Chart.js):
  - Gráfico de barras: ventas últimos 12 meses.
  - Gráfico de dona: ventas por categoría (30 días).
- Productos más vendidos: tabs AlpineJS (`mes`, `semestre`, `año`)
  con tablas.
- Alertas de inventario: agotados y bajo stock (regla: `0 < stock < 2`).

Las etiquetas de los gráficos se inyectan como JSON seguro
(`{{ monthly_labels_json|safe }}`).

## `month_result.html` — Estado de resultados mensual

Renderiza el cálculo de `month_result` con tablas:

- Resumen (ingresos, costos, gastos, otros ingresos, utilidad bruta
  y neta, con %).
- Ingresos y costos por categoría de producto.
- Otros ingresos por categoría y detalle.
- Gastos por categoría y detalle.
- Navegación a meses anteriores.

Usa `humanize` (`intcomma`) para formato de números.

## `user_profile.html` — Perfil

Información de cuenta + `<form action="{% url 'logout' %}">` para
cerrar sesión.

## `import_form.html` — Restaurar datos

`<form enctype="multipart/form-data">` con `<input type="file"
accept=".json" required>`. Tras éxito, redirige a `home` con mensaje
de conteo por modelo.

## `registration/login.html`

`AuthenticationForm` estándar. Pasa el campo `next` si está presente.

## `includes/messages.html`

Renderiza los `messages` de Django como `<article>` descartables con
AlpineJS:

```html
<article x-data="{show : true}" x-show="show">
    {{ message }}
    <button class="delete" ... @click="show=false">
        <i class="material-icons">delete</i>
    </button>
</article>
```

## Filtros de plantilla personalizados

Definidos en `stock/templatetags/getattribute.py`.

### `markdown_safe`

```django
{{ product.description|markdown_safe }}
```

Convierte un string markdown a HTML seguro para renderizar en plantillas.
Implementación en `stock/templatetags/getattribute.py`:

- Usa `markdown.markdown(..., extensions=["nl2br", "fenced_code", "tables"])`.
  La extensión `nl2br` hace que un salto de línea simple se mantenga
  visible (preserva descripciones que ya estaban escritas en texto plano).
- Pasa el HTML resultante por `bleach.clean(...)` con una whitelist
  cerrada de tags y atributos (ver `ALLOWED_TAGS` y `ALLOWED_ATTRIBUTES`
  en el código). Esto evita XSS si la descripción proviene de fuentes
  no controladas.
- Devuelve cadena vacía si el valor es `None` o si ocurre algún error
  de parseo (fallo silencioso).

Es el único filtro del módulo. Usado en `product_detail.html` (dentro
de un contenedor `.product-description` para que los estilos CSS se
apliquen al HTML generado). Si necesitas renderizar markdown en otro
lugar, reutiliza este filtro en lugar de instalar otra cosa.

> **Nota**: el módulo se llama `getattribute.py` por motivos
> históricos (antes contenía los filtros `getattribute` y
> `format_value`, eliminados al migrar las listas a serialización en
> Python). El nombre se conserva para no romper `{% load
> getattribute %}`.

## Convenciones de los templates

- **Sin `<style>`** dentro de ningún template. Todo el estilo va en
  `static/css/styles.css` — ver
  [`docs/estilos.md`](estilos.md).
- **Sin `style="…"`** en HTML. Si necesitas estilos inline, crea una
  clase en `styles.css`.
- **Comentarios multilínea** con `{% comment %} … {% endcomment %}`.
  El token `{# … #}` es de **una sola línea** en Django: si cruza un
  salto de línea, el texto se imprime tal cual en la página.
- **`{% load getattribute %}`** solo en `product_detail.html` (para
  `markdown_safe`).
- **`{% load humanize %}`** en `month_result.html` (para `intcomma`).
- **Iconos** siempre con `<i class="material-icons">nombre</i>` (no con
  font-size inline, salvo casos justificados).
- **Botones** con `<a role="button">…</a>` o `<button type="…">…</button>`
  (Pico los estiliza automáticamente).
- **CSRF**: todos los `<form method="post">` llevan `{% csrf_token %}`.
- **JSON inyectado desde vistas** se marca con `|safe` (ya viene de
  `json.dumps` en Python; el template no serializa).

## Internacionalización

- `LANGUAGE_CODE = 'es-ni'` (español de Nicaragua).
- Todos los textos visibles están escritos directamente en español en
  los templates (no se usa `{% trans %}`). Si más adelante se quiere
  i18n completa, hay que envolver todos los literales.
