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

`stock/urls.py` define todas las rutas de la app. Hay dos patrones:

1. **Rutas explícitas** (`path`) para vistas dedicadas con URL propia
   (`home`, facturas, producto, importar, exportar).
2. **Regex con `re_path`** para el CRUD genérico de modelos simples
   (`category`, `expense`, `expensecategory`, `otherincome`,
   `otherincomecategory`).

## El truco del CRUD genérico

`generic_list_view` y `generic_form_view` resuelven el modelo a partir
de un `model_str` capturado por regex. Internamente usan
`MODEL_NAME_MAP` (en `views.py`):

```python
MODEL_NAME_MAP = {
    "purchase": "PurchaseInvoice",
    "sale": "SaleInvoice",
    "expensecategory": "ExpenseCategory",
    "otherincome": "OtherIncome",
    "otherincomecategory": "OtherIncomeCategory",
    "tag": "Tag",
}
```

Si `model_str` no está en el mapa, se usa `model_str.capitalize()`
(`"category"` → `Category`, `"expense"` → `Expense`, `"customer"` →
`Customer`, etc.).

La vista hace:

```python
model = apps.get_model("stock", model_name)
```

Y luego un `match model_str:` selecciona `fields`, `columns`, `title` y
cómo serializar las filas.

### `valid_models` en cada vista

- `generic_list_view` admite:
  `category`, `product`, `sale`, `purchase`, `expense`,
  `expensecategory`, `otherincome`, `otherincomecategory`,
  `customer`, `tag`.
- `generic_form_view` admite:
  `category`, `expense`, `expensecategory`,
  `otherincome`, `otherincomecategory`, `customer`, `tag`.

> **`product`, `purchase` y `sale` no entran al CRUD genérico de
> formularios**: tienen vistas dedicadas con formularios más complejos
> (formset de fotos, formset de líneas, galería, etc.).

### Añadir un nuevo modelo CRUD simple

1. Crear el modelo en `stock/models.py`.
2. Crear el `ModelForm` en `stock/forms.py`.
3. Registrarlo en el admin (`stock/admin.py`).
4. Añadir la migración: `python manage.py makemigrations stock`.
5. **Actualizar `views.py`**:
   - Si la clave difiere del nombre capitalizado, añadir a
     `MODEL_NAME_MAP`.
   - En `generic_list_view.match`, añadir un `case` con `fields`,
     `columns`, `title`, `queryset`, `page_obj`.
   - En `generic_form_view.match`, añadir un `case` con `form_class`
     y `title`.
   - Añadir el `model_str` a los `valid_models` de ambas vistas.
6. **Actualizar `urls.py`**: añadir el `model_str` a los dos
   `re_path` (list y form).
7. Documentar en [`docs/modelos.md`](modelos.md),
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
| `/<model_str>/` | `list` | `generic_list_view` | Lista genérica del modelo |
| `/<model_str>/new` | `new` | `generic_form_view` | Crear genérico |
| `/<model_str>/<pk>/edit` | `edit` | `generic_form_view` | Editar genérico |
| `/product/new/` | `product_new` | `product_form_view` | Crear producto con fotos |
| `/product/<pk>/` | `product_detail` | `product_detail_view` | Detalle de producto |
| `/product/<pk>/edit/` | `product_edit` | `product_form_view` | Editar producto con fotos |
| `/product/<pk>/toggle-active/` | `product_toggle_active` | `product_toggle_active` | Activar/desactivar producto desde la lista (POST) |
| `/compras/new/` | `purchase_invoice_new` | `purchase_invoice_form_view` | Crear factura de compra |
| `/compras/<pk>/edit/` | `purchase_invoice_edit` | `purchase_invoice_form_view` | Editar factura de compra |
| `/compras/<pk>/` | `purchase_invoice_detail` | `purchase_invoice_detail_view` | Ver factura de compra |
| `/ventas/new/` | `sale_invoice_new` | `sale_invoice_form_view` | Crear factura de venta |
| `/ventas/<pk>/edit/` | `sale_invoice_edit` | `sale_invoice_form_view` | Editar factura de venta |
| `/ventas/<pk>/` | `sale_invoice_detail` | `sale_invoice_detail_view` | Ver factura de venta |
| `/resultados/<offset>/` | `month_result` | `month_result` | Estado de resultados del mes (0 = actual) |
| `/resultados/` | `month_result` | `month_result` | Estado de resultados del mes actual |
| `/reportes/ventas-por-departamento/` | `sales_by_department` | `sales_by_department` | Ventas agrupadas por departamento del cliente (mes actual) |
| `/reportes/ventas-por-departamento/<period>/` | `sales_by_department_period` | `sales_by_department` | Ventas por departamento (períodos: `mes`, `semestre`, `año`, `total`) |
| `/reportes/ventas-por-etiqueta/` | `sales_by_tag` | `sales_by_tag` | Ventas agrupadas por etiqueta del producto (mes actual) |
| `/reportes/ventas-por-etiqueta/<period>/` | `sales_by_tag_period` | `sales_by_tag` | Ventas por etiqueta (períodos: `mes`, `semestre`, `año`, `total`) |
| `/perfil/` | `user_profile` | `user_profile` | Perfil de usuario + logout |
| `/exportar/` | `export_data` | `export_data` | Descargar backup JSON |
| `/importar/` | `import_data` | `import_data` | Subir backup JSON |

`model_str` válido para CRUD genérico: `category`, `product`, `sale`,
`purchase`, `expense`, `expensecategory`, `otherincome`,
`otherincomecategory`, `customer`, `tag`. Para formularios, ver lista
arriba.

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
- **Valor de inventario** = suma de `stock * average_cost` sobre todos
  los productos.
- **Alertas**: productos con `stock=0` y con `0 < stock < 2`.
- **Top productos** (mes, semestre, año) — usa helper `_top_products`.
- **Top categorías** (últimos 30 días).
- **Tendencia mensual** (12 meses hacia atrás): ingresos por mes con
  `TruncMonth`.

### `generic_list_view(request, model_str)`

Ver sección "El truco del CRUD genérico" arriba. Particularidades:

- `purchase` y `sale` se serializan manualmente como filas de
  `[{id, date, party, items_summary, total}]` con totales agregados.
- `product` se serializa por separado para dos tabs (activos /
  inactivos), cada uno como JSON listo para Grid.js. La serialización
  maneja accesos anidados tipo `category__name` recorriendo partes.

### `generic_form_view(request, model_str, pk=None)`

`pk=None` → crear; `pk=int` → editar. Tras un POST válido:

- Si venía de **editar** (`pk` presente): redirige a la lista
  (`redirect("list", model_str=model_str)`). Los modelos del CRUD
  genérico no tienen vista de detalle, así que la lista es la pantalla
  natural para confirmar el cambio.
- Si venía de **crear** (`pk` ausente): redirige al formulario vacío
  (`redirect("new", model_str=model_str)`), igual que antes, para
  permitir el flujo batch de "crear varios seguidos".

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

Vistas dedicadas para facturas. Combinan `*InvoiceForm` con el formset
inline correspondiente:

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

En POST, tras validar form y formset:

- Si **editaba** (`pk` presente): redirige a
  `purchase_invoice_detail` / `sale_invoice_detail` para mostrar la
  factura ya actualizada.
- Si **creaba** (`pk` ausente): redirige a `purchase_invoice_new` /
  `sale_invoice_new` (formulario vacío, igual que antes).

Además, pasan al template `invoice_form.html` los JSON con precios,
costos y stocks de productos activos, que AlpineJS usa para
subtotales en vivo y hints.

### `purchase_invoice_detail_view` / `sale_invoice_detail_view`

Renderizan `invoice_detail.html` con cabecera (`party`, `date`,
`total`) y tabla de líneas. Solo lectura.

### `month_result(request, month_offset=0)`

Estado de resultados de un mes. `month_offset=0` es el mes actual,
`1` es el mes anterior, etc. Usa el helper `month_range_from_offset`
para calcular el rango. Calcula:

- Ingresos, costos, gastos, otros ingresos del mes.
- Utilidad bruta y neta.
- Ingresos y costos **por categoría de producto** (`income_by_category`).
- Gastos y otros ingresos: lista detallada y agrupación por categoría.

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
calcula el porcentaje sobre el total y los serializa como `TopProduct`
(una clase interna con campos pre-formateados). Renderiza `list.html`
con `show_actions=False`.

### `sales_by_department(request, period='mes')`

Reporte que agrupa ventas (`Sale.quantity * Sale.price`) por
`invoice__customer_obj__department__name`. Sirve para ver distribución
geográfica de los ingresos entre los departamentos de Nicaragua.

**Importante**: tras la migración `0013`, todas las facturas tienen
`customer_obj` obligatorio (las que eran "Generic" se asignaron al
"Cliente Genérico"). Por tanto el reporte utiliza **todas** las
facturas; las que tienen como cliente el "Cliente Genérico" sin
departamento quedan agrupadas bajo "Sin departamento".

Períodos soportados: `mes`, `semestre`, `año`, `total`. Renderiza
`list.html` con `show_actions=False`, sin acciones de edición.
Devuelve columnas: `Departamento`, `Unidades Vendidas`, `Ingresos
Totales`, `% por Ingresos`.

### `sales_by_tag(request, period='mes')`

Reporte que agrupa ventas (`Sale.quantity * Sale.price`) por
`product__tags__name`. Permite ver qué etiquetas generan más
ingresos. Excluye ventas cuyo producto no tenga ninguna etiqueta
asignada (`product__tags__isnull=False`).

> A diferencia de `sales_by_department`, este reporte **sí excluye**
> ventas: las de productos sin etiqueta quedan fuera del agrupamiento
> (no aparecen bajo "Sin etiqueta"). Esto es intencional: sin
> etiqueta no hay forma útil de agruparlas.

Períodos soportados: `mes`, `semestre`, `año`, `total`. Renderiza
`list.html` con `show_actions=False`. Columnas: `Etiqueta`,
`Unidades Vendidas`, `Ingresos Totales`, `% por Ingresos`.

### Filtro `?tag=<id>` en `/product/` y `/sale/`

Las listas de productos y ventas aceptan el parámetro `tag` (id de
`Tag`). Si está presente y la etiqueta existe:

- **`/product?tag=<id>`**: muestra solo productos que tengan esa
  etiqueta (la columna "Etiquetas" sigue apareciendo, ahora más
  relevante para identificar el grupo filtrado).
- **`/sale?tag=<id>`**: muestra solo facturas que tengan al menos
  una línea cuyo producto tenga esa etiqueta (`items__product__tags`).

El template `list.html` muestra una barra con un selector de
etiquetas arriba de la tabla cuando hay `available_tags` en el
contexto. Si hay una etiqueta seleccionada, aparece un enlace "Limpiar
filtro" junto al selector. En la lista de productos el selector
convive con los tabs activos/inactivos (preserva el `?tab=...` al
cambiar la etiqueta y viceversa).

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

Top 10 productos por ingresos desde `since`. Devuelve lista de dicts
con `product__name`, `product__category__name`, `total_sold`,
`total_revenue` y `percentage` calculado.

### `_period_label(start, end)`

Etiqueta legible para rango: `'Ene 2026'`, `'Ene – Jun 2026'`,
`'Ene 2025 – Jun 2026'`.

### `month_range_from_offset(month_offset)`

Devuelve `(first_day, last_day)` del mes correspondiente a un offset
positivo (0 = actual, 1 = anterior, etc.). Maneja correctamente el
cambio de año cuando el offset es grande.

---

## Convenciones de las vistas

- Todas devuelven `render(request, "template.html", context)`.
- Tras POST exitoso, usan `redirect(name_url, ...)` y
  `messages.success(request, "Se ha guardado correctamente.")`.
- Errores 404 explícitos con `raise Http404`.
- Sin CBV (vistas basadas en clases). Todo es función.
- Sin mixins ni decoradores personalizados; solo `@login_required`.