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
`home.html`, `list.html` y `invoice_form.html`).

## Estructura de `templates/`

```
templates/
├── layout.html              # Layout base: navbar, CDN, mensajes
├── list.html                # Lista genérica con Grid.js + Alpine (tabs en productos)
├── form.html                # Formulario genérico (1 form por vista)
├── product_form.html        # Producto + formset de fotos (con Alpine mínimo)
├── invoice_form.html        # Factura compra/venta + formset + Alpine para subtotales
├── product_detail.html      # Detalle de producto con galería
├── invoice_detail.html      # Detalle de factura (solo lectura)
├── home.html                # Dashboard: KPIs, gráficos, top productos, alertas
├── month_result.html        # Estado de resultados mensual
├── user_profile.html        # Perfil de usuario + logout
├── import_form.html         # Subida de archivo de respaldo
├── includes/
│   └── messages.html        # Mensajes Django descartables
└── registration/
    └── login.html           # Login estándar
```

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
  - Las tablas (`month_result.html`, `list.html`, formset de facturas)
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

## `list.html` — La lista más usada

Sirve para casi todos los modelos. Tiene dos ramas:

### Rama `model == 'product'`

- Renderiza dos `<div id="gridjs-active">` y `<div id="gridjs-inactive">`.
- AlpineJS controla la visibilidad según `tab`.
- La vista `generic_list_view` pasa `active_data_json` y
  `inactive_data_json` ya serializados.
- La paginación de Grid.js es 25 por página, con búsqueda.
- Los iconos de orden se reemplazan por Material Icons vía callback
  `sort.icon`.
- La columna "Etiquetas" se renderiza con un caso especial en
  `_serialize`: se hace `p.tags.all()` y se concatenan los nombres con
  `, `. El resto de columnas mantiene el recorrido `__`.
- La celda de **Acciones** se serializa como JSON con tres campos
  (`detail`, `edit`, `toggle`) más `active` y `next` (URL actual con
  sus query params). El JS hace `JSON.parse` y renderiza tres iconos:
  `visibility` (ver), `edit` (editar) y un mini-form POST con icono
  `toggle_on`/`toggle_off` (activar/desactivar). El token CSRF se
  inyecta desde un `<input type="hidden" id="csrf-token">` que la
  plantilla añade al inicio de la rama. El `next` se pasa como hidden
  para que la vista `product_toggle_active` redirija de vuelta a la
  lista preservando `?tab=` y `?tag=`.

### Barra de filtro por etiqueta

Las listas de productos y ventas muestran, justo después del botón
"Nuevo", una barra con un selector de etiquetas cuando la vista pasa
`available_tags` en el contexto (ver
[`vistas-y-urls.md`](vistas-y-urls.md#filtro-tagid-en-product-y-sale)).

- Si no hay etiqueta seleccionada: dropdown con "— Todas —" y todas
  las etiquetas. Al cambiar, el form hace submit vía AlpineJS
  (`@change="$event.target.form.submit()"`).
- Si hay etiqueta seleccionada (parámetro `?tag=<id>`): aparece un
  enlace "Limpiar filtro" junto al selector.
- En `/product`, el form lleva un `<input type="hidden" name="tab">`
  con binding a `tab` (AlpineJS) para preservar el tab activo al
  cambiar de etiqueta.

### Rama genérica

- Un solo `<div id="gridjs-table">`.
- La vista serializa `page_obj` recorriendo `columns` (con soporte de
  `__` para acceder a relaciones). El filtro `format_value` (ver más
  abajo) formatea fechas.
- Los enlaces de acción ("Editar", "Ver") se codifican como
  `detail_url|edit_url` en la última celda; Grid.js los separa y crea
  los `<a>` con iconos.
- Para facturas (`purchase`/`sale`), `show_actions` se controla igual
  y los nombres de URL son `purchase_invoice_edit`, etc.

> **Si añades una columna nueva a un modelo que se renderiza con
> `list.html`**, debes:
> 1. Añadir la etiqueta en `fields` y el lookup en `columns` (en la
>    `match` del modelo en `generic_list_view`).
> 2. Si el lookup es `__` (relación), asegúrate de que el filtro
>    `format_value` lo soporte (ya lo hace, pero verifica con datos
>    reales).
> 3. Documentar el cambio en
>    [`docs/mantenimiento.md`](mantenimiento.md).

## `form.html` — Formulario genérico

```html
<form method="post">
    {% csrf_token %}
    {{ form.as_div }}
    <button type="submit">Guardar</button>
</form>
```

`{{ form.as_div }}` renderiza cada campo en un `<div>`. No tiene JS.

Tras guardar, la vista `generic_form_view` redirige a:

- La **lista** del modelo si venía de una edición (`pk` presente).
- Un **formulario vacío** si venía de una creación (`pk` ausente),
  para permitir el flujo batch de "crear varios seguidos".

## `product_form.html` — Producto + fotos

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

## `invoice_form.html` — Factura + líneas (AlpineJS)

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

### `getattribute`

```django
{{ object|getattribute:"name" }}
{{ object|getattribute:"category__name" }}
```

Permite acceder a atributos con notación `__` (Django usa esto para
relaciones en `values()`). Devuelve `""` si algo falla.

> En `list.html` el filtro que se usa es `format_value` (más completo),
> no `getattribute`.

### `format_value`

```django
{{ item|format_value:"date" }}
{{ item|format_value:"category__name" }}
```

Es la versión "inteligente":

- Recorre las partes del lookup (`__`).
- Soporta tanto objetos (`getattr`) como dicts/listas (`__getitem__`).
- Si el resultado es `datetime` → `dd/mm/YYYY HH:MM`.
- Si es `date` → `dd/mm/YYYY`.
- Para otros tipos → `str(value)` o `""` si es `None`.
- Devuelve `""` si algo falla (silencioso).

Este filtro es el que usa `list.html` para renderizar celdas, por eso
se carga con `{% load getattribute %}` al inicio del template.

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
  de parseo (fallo silencioso, análogo a `getattribute`).

Usado en `product_detail.html` (dentro de un contenedor
`.product-description` para que los estilos CSS se apliquen al HTML
generado). Si necesitas renderizar markdown en otro lugar, reutiliza
este filtro en lugar de instalar otra cosa.

## Convenciones de los templates

- **Sin `<style>`** dentro de ningún template. Todo el estilo va en
  `static/css/styles.css` — ver
  [`docs/estilos.md`](estilos.md).
- **Sin `style="…"`** en HTML. Si necesitas estilos inline, crea una
  clase en `styles.css`.
- **`{% load getattribute %}`** al inicio de `list.html` (donde se usa
  `format_value`). Otros templates no lo necesitan.
- **`{% load humanize %}`** en `month_result.html` (para `intcomma`).
- **Iconos** siempre con `<i class="material-icons">nombre</i>` (no con
  font-size inline, salvo casos justificados).
- **Botones** con `<a role="button">…</a>` o `<button type="…">…</button>`
  (Pico los estiliza automáticamente).
- **CSRF**: todos los `<form method="post">` llevan `{% csrf_token %}`.

## Internacionalización

- `LANGUAGE_CODE = 'es-ni'` (español de Nicaragua).
- Todos los textos visibles están escritos directamente en español en
  los templates (no se usa `{% trans %}`). Si más adelante se quiere
  i18n completa, hay que envolver todos los literales.