# Modelos

Documentación de los 10 modelos definidos en `stock/models.py`. Para cada
uno se listan campos, relaciones, opciones `Meta` y métodos relevantes.

> **Importante**: los modelos `Purchase` y `Sale` sobrescriben `save()` y
> `delete()` para mantener `Product.stock` y `Product.average_cost` en
> sincronía. Esa lógica es crítica y se documenta aparte en
> [`logica-stock-costo.md`](logica-stock-costo.md). Léelo antes de tocar
> cualquiera de estos modelos.

## Diagrama de relaciones

```
Category  ──1:N──▶ Product ──1:N──▶ ProductImage
                          │
                          ├──1:N──▶ Purchase ──N:1──▶ PurchaseInvoice
                          │                            (items reverse)
                          │                                │
                          │                                └─ supplier, date
                          │
                          └──1:N──▶ Sale ──N:1──▶ SaleInvoice
                                       (items reverse)
                                            │
                                            ├─ date
                                            └─ customer_obj ──N:1──▶ Customer
                                                                       │
                                                                       └─ department ──N:1──▶ Department

ExpenseCategory ──1:N──▶ Expense
OtherIncomeCategory ──1:N──▶ OtherIncome
```

`Product` es el nodo central. Las facturas (`PurchaseInvoice`, `SaleInvoice`)
agrupan sus líneas (`Purchase`, `Sale`). Los clientes (`Customer`)
pertenecen opcionalmente a un `Department` de Nicaragua y se vinculan
opcionalmente a ventas.

## Category

Categoría de productos. Tabla simple, sin lógica.

| Campo | Tipo | Notas |
|---|---|---|
| `name` | `CharField(max_length=100)` | Nombre único lógico (no hay `unique=True` declarado, depende del uso) |

- `__str__` → `self.name`

## ExpenseCategory

Categoría para gastos operativos.

| Campo | Tipo | Notas |
|---|---|---|
| `name` | `CharField(max_length=100)` | |

- `Meta.ordering = ['name']`
- `__str__` → `self.name`

## Product

Producto del inventario. **Núcleo del sistema**. Su stock y costo promedio
los mantienen `Purchase` y `Sale`.

| Campo | Tipo | Notas |
|---|---|---|
| `name` | `CharField(max_length=200)` | |
| `category` | `ForeignKey(Category, on_delete=CASCADE)` | Borrar categoría borra productos |
| `brand` | `CharField(max_length=100, blank=True)` | Opcional |
| `description` | `TextField(blank=True, null=True)` | Opcional. Acepta markdown; se renderiza con el filtro `markdown_safe` en `product_detail.html` y se sanitiza con `bleach` antes de mostrarse. |
| `stock` | `IntegerField(default=0)` | **Mantenido por `Purchase`/`Sale`** |
| `price` | `DecimalField(max_digits=10, decimal_places=2, default=0)` | Precio de venta |
| `average_cost` | `DecimalField(max_digits=10, decimal_places=2, default=0)` | **Mantenido por `Purchase`** (costo promedio ponderado) |
| `active` | `BooleanField(default=True)` | Soft-delete. Productos inactivos no aparecen en facturas nuevas. Ver migración `0010_product_active`. |

### Métodos

- `update_average_cost(added_quantity, added_cost)` — recalcula
  `average_cost` con la fórmula de promedio ponderado:

  ```
  new_avg = (stock * avg_cost + added_qty * added_cost) / (stock + added_qty)
  ```

  No guarda el producto, solo actualiza el atributo en memoria.
  Quien llama debe persistirlo.

- `__str__` → `self.name`
- `Meta.ordering = ['name', 'category__name']`

## ProductImage

Fotos adjuntas a un producto.

| Campo | Tipo | Notas |
|---|---|---|
| `product` | `ForeignKey(Product, on_delete=CASCADE, related_name="images")` | Borrar producto borra fotos |
| `image` | `ImageField(upload_to="product_images/")` | Requiere `Pillow` |
| `created_at` | `DateTimeField(auto_now_add=True)` | |

- `Meta.ordering = ['-created_at']` (más recientes primero)
- `__str__` → `"Imagen de {product}"`

## PurchaseInvoice

Factura de compra (cabecera). Agrupa una o más líneas `Purchase` del mismo
proveedor.

| Campo | Tipo | Notas |
|---|---|---|
| `created_at` | `DateTimeField(auto_now_add=True)` | |
| `date` | `DateField(default=timezone.now)` | Fecha del documento |
| `supplier` | `CharField(max_length=200, default="Aliexpress")` | Proveedor |

### Métodos

- `get_total()` → suma `item.get_total()` de todas sus líneas
  (`self.items.all()`).
- `__str__` → `"Purchase Invoice #{id} - {supplier}"`
- `Meta.ordering = ['-date']`

## Purchase

Línea de factura de compra. **Sobrescribe `save()` y `delete()`** — ver
[`logica-stock-costo.md`](logica-stock-costo.md).

| Campo | Tipo | Notas |
|---|---|---|
| `created_at` | `DateTimeField(auto_now_add=True)` | |
| `invoice` | `ForeignKey(PurchaseInvoice, on_delete=CASCADE, related_name="items")` | Obligatorio tras migración `0006` |
| `product` | `ForeignKey(Product, on_delete=CASCADE)` | |
| `quantity` | `PositiveIntegerField(default=1)` | |
| `cost` | `DecimalField(max_digits=10, decimal_places=2, default=0)` | Costo unitario de compra |

### Métodos

- `get_total()` → `quantity * cost`
- `save()` → ver doc de lógica de stock/costo
- `delete()` → ver doc de lógica de stock/costo
- `__str__` → `"Purchase #{id} - {quantity} x {product}"`
- `Meta.ordering = ['-created_at']`

## SaleInvoice

Factura de venta (cabecera). Agrupa una o más líneas `Sale` del mismo
cliente.

| Campo | Tipo | Notas |
|---|---|---|
| `created_at` | `DateTimeField(auto_now_add=True)` | |
| `date` | `DateField(default=timezone.now)` | Fecha del documento |
| `customer_obj` | `ForeignKey(Customer, on_delete=PROTECT, related_name="invoices")` | Cliente (obligatorio). Borrar un cliente con facturas asociadas lanza `ProtectedError` |

### Métodos

- `get_total()` → suma `item.get_total()` de sus líneas
- `__str__` → `"Sale Invoice #{id} - {customer}"`
- `Meta.ordering = ['-date']`

## Sale

Línea de factura de venta. **Sobrescribe `save()` y `delete()`** — ver
[`logica-stock-costo.md`](logica-stock-costo.md).

| Campo | Tipo | Notas |
|---|---|---|
| `created_at` | `DateTimeField(auto_now_add=True)` | |
| `invoice` | `ForeignKey(SaleInvoice, on_delete=CASCADE, related_name="items")` | Obligatorio tras migración `0006` |
| `product` | `ForeignKey(Product, on_delete=CASCADE)` | |
| `quantity` | `PositiveIntegerField()` | |
| `price` | `DecimalField(max_digits=10, decimal_places=2)` | Precio unitario al que se vendió |
| `cost` | `DecimalField(max_digits=10, decimal_places=2)` | Costo unitario **al momento de la venta** (copia de `Product.average_cost`) |

> `Sale.cost` se congela al crear/editar la línea. Sirve para que
> `month_result` calcule la utilidad bruta del período sin necesidad de
> recalcular `average_cost` histórico.

### Métodos

- `get_total()` → `quantity * price`
- `save()` → ver doc de lógica de stock/costo
- `delete()` → ver doc de lógica de stock/costo
- `__str__` → `"Sale #{id} - {quantity} x {product}"`
- `Meta.ordering = ['-created_at']`

## Expense

Gasto operativo.

| Campo | Tipo | Notas |
|---|---|---|
| `created_at` | `DateTimeField(auto_now_add=True)` | |
| `date` | `DateField(default=timezone.now)` | |
| `category` | `ForeignKey(ExpenseCategory, on_delete=SET_NULL, null=True, blank=True)` | Opcional; borrar categoría no borra el gasto |
| `description` | `TextField(blank=True, null=True)` | |
| `amount` | `DecimalField(max_digits=10, decimal_places=2, default=0)` | |

- `__str__` → `"C$ {amount} - {description}"`
- `Meta.ordering = ['-created_at']`

## OtherIncomeCategory

Categoría para ingresos que no son ventas (p. ej. intereses, servicios).

| Campo | Tipo | Notas |
|---|---|---|
| `name` | `CharField(max_length=100)` | |

- `Meta.ordering = ['name']`
- `__str__` → `self.name`

## OtherIncome

Ingreso no proveniente de venta.

| Campo | Tipo | Notas |
|---|---|---|
| `created_at` | `DateTimeField(auto_now_add=True)` | |
| `date` | `DateField(default=timezone.now)` | |
| `category` | `ForeignKey(OtherIncomeCategory, on_delete=SET_NULL, null=True, blank=True)` | Opcional |
| `description` | `TextField(blank=True, null=True)` | |
| `amount` | `DecimalField(max_digits=10, decimal_places=2, default=0)` | |

- `__str__` → `"C$ {amount} - {description}"`
- `Meta.ordering = ['-date', '-created_at']`

## Department

Departamento (o región autónoma) de Nicaragua. Catálogo fijo de 17
territorios (15 departamentos + 2 regiones autónomas) que se siembra en
la migración `0011_department_sow_nicaragua`.

| Campo | Tipo | Notas |
|---|---|---|
| `name` | `CharField(max_length=50, unique=True)` | Nombre oficial |
| `code` | `CharField(max_length=3, unique=True)` | Sigla corta (`MAN`, `MAS`, `RACCN`, `RACCS`...) |

- `Meta.ordering = ['name']`
- `__str__` → `self.name`

> La gestión CRUD se hace desde el admin de Django. La tabla no está
> pensada para editar desde la UI pública (la lista de territorios es
> estable).

## Customer

Cliente del negocio. Permite registrar datos de contacto y demográficos
útiles para análisis y reportes. **Se vincula opcionalmente** a una
factura de venta mediante `SaleInvoice.customer_obj`.

| Campo | Tipo | Notas |
|---|---|---|
| `name` | `CharField(max_length=200)` | Nombre del cliente (obligatorio) |
| `whatsapp` | `CharField(max_length=20, blank=True)` | No WhatsApp (con prefijo internacional, p. ej. `+505 8888 8888`) |
| `address` | `CharField(max_length=300, blank=True)` | Dirección física |
| `department` | `ForeignKey(Department, on_delete=SET_NULL, null=True, blank=True)` | Departamento de Nicaragua; borrar depto no borra clientes |
| `notes` | `TextField(blank=True, null=True)` | Comentarios libres |
| `active` | `BooleanField(default=True)` | Soft-delete. Los inactivos no aparecen como opción en ventas nuevas |
| `created_at` | `DateTimeField(auto_now_add=True)` | Sirve para KPI "Clientes nuevos del mes" del dashboard |

- `Meta.ordering = ['name']`
- `__str__` → `self.name`

> **Vinculación con ventas**: `SaleInvoice.customer_obj` es la única
> vía de asociación con el cliente. La migración `0013` eliminó el
> campo de texto `customer` que existía antes; las facturas con
> `customer='Generic'` o vacío quedaron asignadas a un
> `Customer` llamado "Cliente Genérico" que actúa como
> marcador de posición para ventas sin cliente identificado.

## Resumen de comportamiento `on_delete`

| Relación | `on_delete` | Efecto |
|---|---|---|
| `Product.category → Category` | `CASCADE` | Borrar categoría borra productos |
| `ProductImage.product → Product` | `CASCADE` | Borrar producto borra fotos |
| `Purchase.invoice → PurchaseInvoice` | `CASCADE` | Borrar factura borra sus líneas (lo que a su vez revierte stock vía `delete()`) |
| `Purchase.product → Product` | `CASCADE` | Borrar producto borra compras |
| `Sale.invoice → SaleInvoice` | `CASCADE` | Borrar factura borra sus líneas |
| `Sale.product → Product` | `CASCADE` | Borrar producto borra ventas |
| `Expense.category → ExpenseCategory` | `SET_NULL` | Borrar categoría deja el gasto huérfano (sin categoría) |
| `OtherIncome.category → OtherIncomeCategory` | `SET_NULL` | Igual |
| `SaleInvoice.customer_obj → Customer` | `PROTECT` | Borrar cliente con facturas asociadas lanza `ProtectedError` (preserva historial) |
| `Customer.department → Department` | `SET_NULL` | Borrar departamento deja el cliente sin depto |

> **Advertencia**: como `Purchase` y `Sale` tienen `CASCADE` desde sus
> facturas, y al borrar ejecutan `delete()` que revierte stock, **borrar
> una factura es seguro**: el stock se ajusta correctamente. Lo que sí
> hay que evitar es borrar productos directamente sin querer, porque
> arrastra todas sus compras y ventas.