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
                                            └─ customer, date

ExpenseCategory ──1:N──▶ Expense
OtherIncomeCategory ──1:N──▶ OtherIncome
```

`Product` es el nodo central. Las facturas (`PurchaseInvoice`, `SaleInvoice`)
agrupan sus líneas (`Purchase`, `Sale`).

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
| `description` | `TextField(blank=True, null=True)` | Opcional |
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
| `customer` | `CharField(max_length=200, default="Generic")` | Cliente |

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

> **Advertencia**: como `Purchase` y `Sale` tienen `CASCADE` desde sus
> facturas, y al borrar ejecutan `delete()` que revierte stock, **borrar
> una factura es seguro**: el stock se ajusta correctamente. Lo que sí
> hay que evitar es borrar productos directamente sin querer, porque
> arrastra todas sus compras y ventas.