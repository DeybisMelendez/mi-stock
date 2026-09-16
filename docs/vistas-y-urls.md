# Vistas y URLs

Catálogo de vistas definidas en `stock/views.py` y su mapeo en
`stock/urls.py`. Todas las vistas (salvo error 404 explícito) llevan
`@login_required`. **Excepción**: la API pública de productos
(`stock/api.py`), que es de solo lectura y no requiere login — ver
[`api.md`](api.md).

## Cómo se compone el routing

`mistock/urls.py` monta tres cosas a nivel raíz:

```python
path('admin/', admin.site.urls),
path('accounts/', include('django.contrib.auth.urls')),
path("", include("stock.urls")),
```

`stock/urls.py` define todas las rutas de la app con `path()` explícitos.
**No hay vistas genéricas ni regex**: cada modelo simple tiene su vista
de lista, su vista de formulario y sus tres rutas propias.

## Convención de nombres

Para cada modelo CRUD simple `m` (en minúsculas, p. ej. `category`):

| Elemento | Patrón | Ejemplo |
|---|---|---|
| Vista de lista | `<m>_list_view` | `category_list_view` |
| Vista de formulario | `<m>_form_view` | `expense_form_view` |
| Nombre URL lista | `<m>_list` | `tag_list` |
| Nombre URL crear | `<m>_new` | `customer_new` |
| Nombre URL editar | `<m>_edit` | `expense_edit` |
| Template lista | `<m>_list.html` | `category_list.html` |
| Template formulario | `<m>_form.html` | `tag_form.html` |

Las URLs siguen el patrón `/m/`, `/m/new/`, `/m/<pk>/edit/` (con slash
final, consistente con las vistas dedicadas históricas).

Las vistas de lista serializan las filas **en Python** (no en el
template): cada vista construye `headers_json` (encabezados) y
`data_json` (filas como arrays; la última celda es un objeto de
acciones `{"detail": ..., "edit": ...}` cuando aplica) y se los pasa al
parcial `includes/grid_table.html`, que monta Grid.js. Ver
[`frontend.md`](frontend.md).

## Añadir un nuevo modelo CRUD simple

1. Crear el modelo en `stock/models.py`.
2. Crear el `ModelForm` en `stock/forms.py`.
3. Registrarlo en el admin (`stock/admin.py`).
4. Añadir la migración: `python manage.py makemigrations stock`.
5. **Crear las vistas dedicadas** en `views.py`:
   `<m>_list_view` (serializa filas a `headers_json`/`data_json`) y
   `<m>_form_view` (patrón: `pk=None` crea, `pk` edita).
6. **Crear los templates** `<m>_list.html` y `<m>_form.html`
   (reutilizando el parcial `grid_table.html`).
7. **Actualizar `urls.py`**: las tres rutas `path()` explícitas.
8. Añadir el enlace al menú en `templates/layout.html`.
9. Documentar en [`docs/modelos.md`](modelos.md),
   [`docs/vistas-y-urls.md`](vistas-y-urls.md) y
   [`docs/mantenimiento.md`](mantenimiento.md).

---

## Mapa URL → vista

| URL | Nombre | Vista | Descripción |
|---|---|---|---|
| `/` | `home` | `home` | Dashboard con KPIs, gráficos y top productos |
| `/favicon.ico` | — | lambda | Devuelve 404 (no hay favicon) |
| `/api/products/` | `api_product_list` | `api_product_list` | API pública: lista de productos disponibles (ver [`api.md`](api.md)) |
| `/api/products/<pk>/` | `api_product_detail` | `api_product_detail` | API pública: detalle de producto (ver [`api.md`](api.md)) |
| `/top-productos/<period>/` | `top_products_period` | `top_products_view` | Top productos por período (ver abajo) |
| `/top-productos/` | `top_products` | `top_products_view` | Top productos del mes (default `period="mes"`) |
| `/product/` | `product_list` | `product_list_view` | Lista de productos con tabs activos/inactivos |
| `/category/` | `category_list` | `category_list_view` | Lista de categorías |
| `/tag/` | `tag_list` | `tag_list_view` | Lista de etiquetas |
| `/customer/` | `customer_list` | `customer_list_view` | Lista de clientes |
| `/expensecategory/` | `expensecategory_list` | `expensecategory_list_view` | Lista de categorías de gastos |
| `/otherincomecategory/` | `otherincomecategory_list` | `otherincomecategory_list_view` | Lista de categorías de otros ingresos |
| `/expense/` | `expense_list` | `expense_list_view` | Lista de gastos |
| `/otherincome/` | `otherincome_list` | `otherincome_list_view` | Lista de otros ingresos |
| `/compras/` | `purchase_list` | `purchase_list_view` | Lista de facturas de compra |
| `/ventas/` | `sale_list` | `sale_list_view` | Lista de facturas de venta |
| `/product/new/` | `product_new` | `product_form_view` | Crear producto con fotos |
| `/product/<pk>/` | `product_detail` | `product_detail_view` | Detalle de producto |
| `/product/<pk>/edit/` | `product_edit` | `product_form_view` | Editar producto con fotos |
| `/product/<pk>/toggle-active/` | `product_toggle_active` | `product_toggle_active` | Activar/desactivar producto desde la lista (POST) |
| `/compras/new/` | `purchase_invoice_new` | `purchase_invoice_new_view` | Crear factura de compra |
| `/compras/<pk>/edit/` | `purchase_invoice_edit` | `purchase_invoice_form_view` | **Devuelve 404**: edición deshabilitada |
| `/compras/<pk>/` | `purchase_invoice_detail` | `purchase_invoice_detail_view` | Ver factura de compra (con acciones Anular/Reactivar) |
| `/compras/<pk>/anular/` | `void_purchase_invoice` | `void_purchase_invoice` | Anular factura de compra (POST, requiere razón) |
| `/compras/<pk>/reactivar/` | `reactivate_purchase_invoice` | `reactivate_purchase_invoice` | Reactivar factura de compra (POST) |
| `/ventas/new/` | `sale_invoice_new` | `sale_invoice_new_view` | Crear factura de venta |
| `/ventas/<pk>/edit/` | `sale_invoice_edit` | `sale_invoice_form_view` | **Devuelve 404**: edición deshabilitada |
| `/ventas/<pk>/` | `sale_invoice_detail` | `sale_invoice_detail_view` | Ver factura de venta (con acciones Anular/Reactivar) |
| `/ventas/<pk>/anular/` | `void_sale_invoice` | `void_sale_invoice` | Anular factura de venta (POST, requiere razón) |
| `/ventas/<pk>/reactivar/` | `reactivate_sale_invoice` | `reactivate_sale_invoice` | Reactivar factura de venta (POST) |
| `/resultados/<offset>/` | `month_result` | `month_result` | Estado de resultados del mes (0 = actual) |
| `/resultados/` | `month_result` | `month_result` | Estado de resultados del mes actual |
| `/reportes/ventas-por-departamento/` | `sales_by_department` | `sales_by_department` | Ventas agrupadas por departamento del cliente (mes actual) |
| `/reportes/ventas-por-departamento/<period>/` | `sales_by_department_period` | `sales_by_department` | Ventas por departamento (períodos: `mes`, `semestre`, `año`, `total`) |
| `/reportes/ventas-por-etiqueta/` | `sales_by_tag` | `sales_by_tag` | Ventas agrupadas por etiqueta del producto (mes actual) |
| `/reportes/ventas-por-etiqueta/<period>/` | `sales_by_tag_period` | `sales_by_tag` | Ventas por etiqueta (períodos: `mes`, `semestre`, `año`, `total`) |
| `/perfil/` | `user_profile` | `user_profile` | Perfil de usuario + logout |
| `/exportar/` | `export_data` | `export_data` | Descargar backup JSON |
| `/importar/` | `import_data` | `import_data` | Subir backup JSON |

Para cada modelo simple `m` de
`category`, `tag`, `customer`, `expensecategory`,
`otherincomecategory`, `expense`, `otherincome` existen además:

| URL | Nombre | Vista |
|---|---|---|
| `/m/new/` | `m_new` | `m_form_view` |
| `/m/<pk>/edit/` | `m_edit` | `m_form_view` |

---

## API pública (sin login)

Las vistas `api_product_list` y `api_product_detail` viven en
`stock/api.py` (no en `views.py`), **no llevan `@login_required`** y
usan `@require_GET` (cualquier otro método → 405). Devuelven JSON con
el catálogo de productos disponibles (`active=True` y `stock > 0`),
excluyendo `average_cost` y `stock` del payload.

La referencia completa (formato, ejemplos, CORS) está en
[`api.md`](api.md).

---

## Vistas CRUD de modelos simples

Cada uno de los 7 modelos simples tiene un par de vistas dedicadas que
siguen el mismo patrón (ver "Convención de nombres"):

- **Lista** (`<m>_list_view`): consulta el modelo, serializa cada fila
  a un array de strings y añade como última celda el objeto de acciones
  `{"edit": ...}`. Renderiza su template `<m>_list.html`, que coloca el
  botón "Nuevo" y delega la tabla al parcial `grid_table.html`.
- **Formulario** (`<m>_form_view`, `pk=None`): un `ModelForm` del
  modelo. Tras POST válido muestra `messages.success` y redirige:
  - Si **editaba** (`pk` presente): a la lista del modelo.
  - Si **creaba** (`pk` ausente): al formulario vacío (flujo batch de
    "crear varios seguidos").

Particularidades por modelo:

- `category`, `tag`, `expensecategory`, `otherincomecategory`: lista de
  una sola columna (`name`); formulario de un campo.
- `customer`: lista con `Nombre`, `WhatsApp`, `Departamento` y `Activo`
  (serializado como "Sí"/"No"); usa `select_related("department")`.
- `expense` / `otherincome`: lista con `Fecha` (`dd/mm/YYYY`),
  `Categoría`, `Descripción`, `Monto`; usa `select_related("category")`.

## Vistas dedicadas

### `home(request)` — Dashboard

Calcula y devuelve al template `home.html`:

- **Períodos calendario**: mes actual, mes anterior, semestre (Ene–Jun o
  Jul–Dic según el mes actual), año, últimos 30 días.
- **Ingresos** (suma de `quantity * price` de `Sale` filtrada por
  `invoice__date`) para cada período.
- **Costos** del mes (suma de `quantity * cost`).
- **Gastos del mes** (suma de `Expense.amount`).
- **Otros ingresos del mes** (suma de `OtherIncome.amount`).
- **Clientes nuevos del mes** (cuenta de `Customer` con
  `created_at` en el mes en curso, más el crecimiento vs mes anterior).
- **Ganancia bruta** = ingresos − costos.
- **Ganancia neta** = ingresos + otros ingresos − costos − gastos.
- **Valor de inventario** = suma de `stock * average_cost` solo sobre
  productos **activos**. Los inactivos (`active=False`) no se
  contabilizan: ya no forman parte del catálogo disponible.
- **Top productos** (mes, semestre, año) — usa helper `_top_products`.
- **Top categorías** (últimos 30 días).
- **Tendencia mensual** (12 meses hacia atrás): ingresos por mes con
  `TruncMonth`.

> **Productos inactivos excluidos**: todas las queries sobre `Sale`
> (ingresos, costos, top productos, top categorías, tendencia mensual)
> añaden `product__active=True`. Las queries sobre `Product` (valor de
> inventario, alertas) añaden `active=True`. Esto es coherente con el
> comportamiento de los formularios de facturas y la API pública, que
> también filtran por `active=True`. Si luego reactivas un producto,
> sus ventas pasadas vuelven a contar en los reportes históricos.

### `product_list_view(request)`

Lista de productos con dos tabs (activos / inactivos) controlados por
AlpineJS y filtro opcional `?tag=<id>`. Serializa cada tab a JSON
(`active_data_json` / `inactive_data_json`); la última celda de cada
fila lleva el objeto de acciones `{"detail", "edit", "toggle", "active",
"next"}` que el parcial Grid.js convierte en iconos (ver + editar +
mini-form POST de activar/desactivar). Renderiza `product_list.html`.

### `purchase_list_view(request)` / `sale_list_view(request)`

Listas de facturas. Cada fila serializa `Fecha` (`dd/mm/YYYY`), parte
(`supplier` o `customer_obj.name`), resumen de líneas
(`cantidad × producto`), total y estado (`Activa` / `Anulada`).
Aceptan filtro opcional `?tag=<id>` (facturas con al menos una
línea cuyo producto tenga la etiqueta). Renderizan
`purchase_list.html` / `sale_list.html`.

> **Anular/Reactivar no se exponen en los listados**: las listas solo
> muestran el botón "Ver" para cada fila. Para anular o reactivar
> una factura hay que entrar a su detalle
> (`/compras/<pk>/`, `/ventas/<pk>/`). Ver
> [`invoice_detail.html`](../templates/invoice_detail.html) y la
> nota de "Anular/Reactivar solo desde el detalle" bajo
> `void_purchase_invoice`.

### `product_form_view(request, pk=None)`

Vista dedicada para `Product`. Combina `ProductForm` con
`ProductImageFormSet` (definido en `forms.py`). En POST:

1. Valida form y formset.
2. `form.save()` (crea o edita el producto).
3. `formset.instance = product` y `formset.save()` (gestiona fotos).
4. Redirige:
   - Si **editaba** (`pk` presente): a `product_detail` del producto
     recién guardado, para mostrar el resultado de los cambios (fotos,
     stock, precio, margen...).
   - Si **creaba** (`pk` ausente): a `product_new` (formulario vacío),
     igual que antes.

### `product_detail_view(request, pk)`

Detalle de un producto. Calcula agregados de `Sale` y `Purchase`:

- `total_sold`, `total_revenue`, `last_sale`
- `total_bought`, `total_spent`, `last_purchase`
- Margen unitario y porcentaje
- Valor en inventario (`stock * average_cost`)

Pasa además `edit_url` y `list_url` para los botones del template.

### `product_toggle_active(request, pk)`

Activa o desactiva un producto desde la lista sin entrar al formulario
de edición. Decorada con `@login_required` y `@require_POST` (cualquier
GET → 405).

- Invierte `Product.active`, persiste solo ese campo con
  `save(update_fields=["active"])` (no toca stock ni costo).
- Manda `messages.success` con "Producto activado/desactivado
  correctamente.".
- Redirige a `request.POST["next"]` si está presente (preserva tab y
  filtros aplicados, p. ej. `?tab=inactive&tag=3`); si no, a
  `/product/`.

El botón en la lista es un mini-form POST con icono `toggle_on` /
`toggle_off` (ver [`frontend.md`](frontend.md#rama-model--product)).

### `purchase_invoice_form_view` / `sale_invoice_form_view`

**Stubs que devuelven `Http404`**. Las facturas ya no se editan en
la UI: para corregir una hay que anularla y crear una nueva. Las
funciones se conservan (y los nombres de URL también) para que
cualquier `reverse("purchase_invoice_edit", ...)` que quede en
código no rompa, pero `/compras/<pk>/edit/` y `/ventas/<pk>/edit/`
responden 404. La creación de facturas se hace vía
`purchase_invoice_new_view` / `sale_invoice_new_view`.

### `purchase_invoice_new_view` / `sale_invoice_new_view`

Vistas dedicadas para **crear** facturas. Combinan `*InvoiceForm`
con el formset inline correspondiente:

```python
PurchaseItemFormSet = inlineformset_factory(
    PurchaseInvoice, Purchase, PurchaseItemForm,
    extra=1, can_delete=True,
)
SaleItemFormSet = inlineformset_factory(
    SaleInvoice, Sale, SaleItemForm,
    extra=1, can_delete=True,
)
```

> Estos formsets están definidos en `views.py`, **no** en `forms.py`.

En POST, tras validar form y formset, `form.save()` y luego
`formset.instance = invoice; formset.save()`. Redirige al
formulario vacío (`purchase_invoice_new` / `sale_invoice_new`)
para permitir el flujo batch de "crear varios seguidos".

Además, pasan al template `invoice_form.html` los JSON con precios,
costos y stocks de productos activos, que AlpineJS usa para
subtotales en vivo y hints.

### `void_purchase_invoice` / `void_sale_invoice`

Anulan una factura. Vistas con `@login_required` y `@require_POST`.

- Leen `reason` de `request.POST`. Si está vacío, redirigen al
  detalle con `messages.error`.
- Si la factura ya estaba anulada, redirigen al detalle con
  `messages.info`.
- Llaman a `invoice.void(request.user, reason)`. Este método crea
  snapshots en `VoidedInvoiceLine`, borra las líneas (cuyo
  `delete()` revierte stock/costo) y marca la factura como
  anulada.
- Redirigen a la lista del modelo con `messages.success`.

> **Anular/Reactivar solo desde el detalle.** Las vistas
> `void_*_invoice` y `reactivate_*_invoice` **no** se enlazan desde
> los listados (`/compras/`, `/ventas/`): las listas solo exponen
> el botón "Ver" para cada fila. Para anular o reactivar hay que
> entrar al detalle de la factura. Esto simplifica la UX (la razón
> obligatoria se pide una vez que el usuario ya está mirando la
> factura) y elimina la posibilidad de enviar formularios vacíos
> desde la lista por error. Ver
> [`invoice_detail.html`](../templates/invoice_detail.html).

### `reactivate_purchase_invoice` / `reactivate_sale_invoice`

Revierten la anulación. Vistas con `@login_required` y
`@require_POST`.

- Si la factura no está anulada, redirige al detalle con
  `messages.info`.
- Llama a `invoice.reactivate()`. Este método lee los snapshots
  de `VoidedInvoiceLine`, recrea las líneas (vía `Purchase.save()`
  o `Sale.save()` que re-aplican stock/costo) y limpia los campos
  `voided*` de la factura.
- Redirige al detalle con `messages.success`.

### `purchase_invoice_detail_view` / `sale_invoice_detail_view`

Renderizan `invoice_detail.html` con cabecera (`party`, `date`,
`total`) y tabla de líneas. Si la factura está anulada, muestran un
banner con fecha, usuario y razón. Solo lectura, con botones
"Anular" o "Reactivar" según el estado.

### `month_result(request, month_offset=0)`

Estado de resultados de un mes. `month_offset=0` es el mes actual,
`1` es el mes anterior, etc. Usa el helper `month_range_from_offset`
para calcular el rango. Calcula:

- Ingresos, costos, gastos, otros ingresos del mes.
- Utilidad bruta y neta.
- Ingresos y costos **por categoría de producto** (`income_by_category`).
- Gastos y otros ingresos: lista detallada y agrupación por categoría.

> **Productos inactivos excluidos**: las queries sobre `Sale` (ingresos,
> costos, `income_by_category`) añaden `product__active=True`. Los
> gastos y otros ingresos no se ven afectados (no están ligados a
> productos). Si reactivas un producto, sus ventas vuelven a contar
> en el mes correspondiente.

El template `month_result.html` muestra navegación entre meses
anteriores (no permite ir a futuro).

### `top_products_view(request, period)`

Top productos vendidos en un período. `period` puede ser:

- `"hoy"` — desde hoy
- `"semana"` — últimos 7 días
- `"mes"` — desde el día 1 del mes
- `"semestre"` — desde el inicio del semestre (Ene o Jul)
- `"año"` — desde el 1 de enero
- `"total"` — todo el histórico

Agrupa por producto, suma cantidad e ingresos (`quantity * price`),
calcula el porcentaje sobre el total y serializa las filas a
`data_json`. **Excluye productos inactivos** (`product__active=True`).
Renderiza `top_products.html` con el parcial `grid_table.html`
(`no_actions=True`, sin columna de acciones) y el parcial
`period_nav.html` para saltar entre períodos.

### `sales_by_department(request, period='mes')`

Reporte que agrupa ventas (`Sale.quantity * Sale.price`) por
`invoice__customer_obj__department__name`. Sirve para ver distribución
geográfica de los ingresos entre los departamentos de Nicaragua.

**Importante**: tras la migración `0013`, todas las facturas tienen
`customer_obj` obligatorio (las que eran "Generic" se asignaron al
"Cliente Genérico"). Por tanto el reporte utiliza **todas** las
facturas; las que tienen como cliente el "Cliente Genérico" sin
departamento quedan agrupadas bajo "Sin departamento".

**Excluye productos inactivos** (`product__active=True`): solo se
contabilizan ventas de productos activos.

Períodos soportados: `mes`, `semestre`, `año`, `total`. Renderiza
`sales_by_department.html` con `grid_table.html` (`no_actions=True`,
sin acciones de edición) y `period_nav.html`. Columnas: `Departamento`,
`Unidades Vendidas`, `Ingresos Totales`, `% por Ingresos`.

### `sales_by_tag(request, period='mes')`

Reporte que agrupa ventas (`Sale.quantity * Sale.price`) por
`product__tags__name`. Permite ver qué etiquetas generan más
ingresos. Excluye ventas cuyo producto no tenga ninguna etiqueta
asignada (`product__tags__isnull=False`).

> A diferencia de `sales_by_department`, este reporte **sí excluye**
> ventas: las de productos sin etiqueta quedan fuera del agrupamiento
> (no aparecen bajo "Sin etiqueta"). Esto es intencional: sin
> etiqueta no hay forma útil de agruparlas.

**Excluye productos inactivos** (`product__active=True`): si un
producto está inactivo, sus ventas (con o sin etiqueta) quedan fuera
del agrupamiento.

Períodos soportados: `mes`, `semestre`, `año`, `total`. Renderiza
`sales_by_tag.html` con `grid_table.html` (`no_actions=True`) y
`period_nav.html`. Columnas: `Etiqueta`, `Unidades Vendidas`,
`Ingresos Totales`, `% por Ingresos`.

### Filtro `?tag=<id>` en `/product/`, `/compras/` y `/ventas/`

Las listas de productos, compras y ventas aceptan el parámetro `tag`
(id de `Tag`). Si está presente y la etiqueta existe:

- **`/product/?tag=<id>`**: muestra solo productos que tengan esa
  etiqueta (la columna "Etiquetas" sigue apareciendo, ahora más
  relevante para identificar el grupo filtrado).
- **`/compras/?tag=<id>`** y **`/ventas/?tag=<id>`**: muestran solo
  facturas que tengan al menos una línea cuyo producto tenga esa
  etiqueta (`items__product__tags`).

El parcial `includes/tag_filter.html` (incluido por
`product_list.html`, `purchase_list.html` y `sale_list.html`) muestra
la barra con el selector de etiquetas. Si hay una etiqueta
seleccionada, aparece un enlace "Limpiar filtro" junto al selector. En
la lista de productos el selector convive con los tabs activos/
inactivos (preserva el `?tab=...` al cambiar la etiqueta y
viceversa).

El filtro es opcional. Sin él, las listas muestran todos los
registros (etiquetados o no).

### `user_profile(request)`

Renderiza `user_profile.html` con datos del usuario actual y un botón
para `POST` a `logout`.

### `export_data(request)`

Genera un JSON con todos los modelos en `models_to_export` (orden
definido, ver [`docs/importar-exportar.md`](importar-exportar.md)).
Devuelve el archivo como `HttpResponse` con
`Content-Disposition: attachment; filename="mi-stock-backup-YYYYMMDD-HHMMSS.json"`.

### `import_data(request)`

Acepta un archivo subido en `backup_file`. Lo decodifica y reimporta
modelo por modelo con `serializers.deserialize`. Ver
[`docs/importar-exportar.md`](importar-exportar.md).

---

## Helpers internos

### `_top_products(since)`

Top 10 productos por ingresos desde `since`. **Excluye productos
inactivos** (`product__active=True`). Devuelve lista de dicts con
`product__name`, `product__category__name`, `total_sold`,
`total_revenue` y `percentage` calculado.

### `_period_label(start, end)`

Etiqueta legible para rango: `'Ene 2026'`, `'Ene – Jun 2026'`,
`'Ene 2025 – Jun 2026'`.

### `month_range_from_offset(month_offset)`

Devuelve `(first_day, last_day)` del mes correspondiente a un offset
positivo (0 = actual, 1 = anterior, etc.). Maneja correctamente el
cambio de año cuando el offset es grande.

### `REPORT_PERIODS`

Constante con los pares `(clave, etiqueta)` de los períodos de los
reportes (`hoy`, `semana`, `mes`, `semestre`, `año`, `total`). La usan
las tres vistas de reportes para alimentar al parcial `period_nav.html`.

---

## Convenciones de las vistas

- Todas devuelven `render(request, "template.html", context)`.
- Las listas serializan filas en Python (`headers_json` + `data_json`)
  y delegan la tabla al parcial `grid_table.html`. Si la lista tiene
  columnas numéricas, además pasan `sort_values_json` (lista paralela
  con floats en columnas numéricas y `""` en el resto) y envuelven
  las celdas numéricas con `_sortable_cell(value)` para que Grid.js
  ordene numéricamente. Ver
  [`frontend.md`](frontend.md#celdas-ordenables-columnas-numéricas).
- Tras POST exitoso, usan `redirect(name_url, ...)` y
  `messages.success(request, "Se ha guardado correctamente.")`.
- Errores 404 explícitos con `raise Http404`.
- Sin CBV (vistas basadas en clases). Todo es función.
- Sin mixins ni decoradores personalizados; solo `@login_required`.
