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
la barra de navegación:

- Si `user.is_authenticated`: dropdown agrupado (Catálogo / Operaciones
  / Reportes / Cuenta / Datos).
- Si no: enlace "Iniciar sesión".

Debajo del `<nav>`:

```html
{% include "includes/messages.html" %}
{% block content %}{% endblock %}
```

Y al final del `<body>` se cargan los scripts de Alpine y Grid.js.

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

## `product_form.html` — Producto + fotos

- Form principal `ProductForm` (campos del producto).
- Formset `ProductImageFormSet` para múltiples fotos.
- Botón "+ Agregar foto" usa un pequeño JS inline (`addItemRow()`) que
  clona una fila de la plantilla oculta `#empty-row-template` y
  incrementa `TOTAL_FORMS`.
- Muestra thumbnails de fotos existentes en el formset de edición.

## `invoice_form.html` — Factura + líneas (AlpineJS)

La más interactiva. Renderiza:

- Cabecera de la factura (`PurchaseInvoiceForm` o `SaleInvoiceForm`).
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