# Lógica de stock y costo promedio

> **Esta es la parte más sensible del proyecto.** Toda la mutación de
> `Product.stock` y `Product.average_cost` ocurre dentro de los métodos
> `save()` y `delete()` de `Purchase` y `Sale` (`stock/models.py`). No
> hay signals ni vistas que lo hagan. Cualquier cambio debe preservar la
> lógica de **revertir-y-aplicar** o el inventario se desincroniza.

## Por qué está en el modelo y no en signals

- **Atomicidad**: cada `save()`/`delete()` de una línea ejecuta sus
  mutaciones sobre `Product` antes de persistir. Una transacción cubre
  toda la operación.
- **Cobertura universal**: las mutaciones se aplican siempre, sin
  importar si la línea se crea desde una vista, el admin de Django, un
  comando de gestión o un script.
- **Reversión en edición**: al editar una compra o venta, primero se
  revierte el efecto viejo y luego se aplica el nuevo. Hacer esto desde
  la vista requeriría replicar la lógica en cada lugar donde se puede
  editar.

`Purchase` y `Sale` se apoyan en `Product.update_average_cost(q, c)`:

```python
total_cost = (self.stock * self.average_cost) + (added_quantity * added_cost)
total_quantity = self.stock + added_quantity
self.average_cost = total_cost / total_quantity
```

Promedio ponderado clásico.

---

## `Purchase.save()` — Compra nueva vs edición

### Caso A — Creación (`pk` is None)

```python
self.product.update_average_cost(self.quantity, self.cost)
self.product.stock += self.quantity
self.product.save()
super().save(*args, **kwargs)
```

- Suma el stock.
- Recalcula el costo promedio.
- Persiste la línea.

### Caso B — Edición (mismo producto, mismas cantidad y costo)

Si nada cambió realmente, simplemente `super().save()` y salir. Esta
optimización evita trabajo innecesario cuando el formulario se reenvía
sin modificaciones.

### Caso C — Edición (cambia producto, cantidad o costo)

Primero **revierte** el efecto viejo sobre el producto viejo:

```python
if old_prod.stock - old.quantity > 0:
    old_prod.average_cost = (
        (old_prod.stock * old_prod.average_cost - old.quantity * old.cost)
        / (old_prod.stock - old.quantity)
    )
else:
    old_prod.average_cost = 0
old_prod.stock -= old.quantity
old_prod.save()
```

Si el stock quedaría en 0 (o menos), se resetea `average_cost` a 0 para
evitar división por cero.

Luego **aplica** el efecto nuevo:

- **Producto diferente**: usa el producto nuevo como destino del stock
  y el recálculo de costo.
- **Mismo producto**: reutiliza `old_prod` (ya revertido) y aplica la
  nueva compra encima. Al final reasigna `self.product = old_prod`
  para que la FK siga apuntando al mismo objeto en memoria.

> **Por qué importa**: si omites la reversión, una edición acumula
> efectos. Si omites la rama de "stock quedaría en cero", Python lanza
> `ZeroDivisionError` al recalcular.

---

## `Purchase.delete()` — Borrar una línea

```python
product = self.product
if product.stock - self.quantity > 0:
    total_value = (product.stock * product.average_cost) - (self.quantity * self.cost)
    new_quantity = product.stock - self.quantity
    product.average_cost = total_value / new_quantity
else:
    product.average_cost = 0
product.stock -= self.quantity
self.product.save()
super().delete(*args, **kwargs)
```

- Resta el stock.
- "Deshace" la contribución de esta línea al promedio ponderado
  (fórmula simétrica a `update_average_cost`).
- Si tras restar el stock queda en cero, fuerza `average_cost = 0`.
- Persiste el cambio y luego borra la línea.

---

## `Sale.save()` — Venta nueva vs edición

> Las ventas **no recalculan `average_cost`**; solo mueven stock. El
> costo se congela en `Sale.cost` copiando `Product.average_cost` al
> momento de la venta (o de la edición).
>
> El precio de la línea es **editable por línea** (override ad-hoc
> del precio de catálogo). `Sale.save()` respeta el `self.price` que
> llega del form y **no** lo sobreescribe con `Product.price`. Esto
> permite vender a un precio distinto (descuento, negociación,
> cliente especial) sin modificar el precio del producto en el
> catálogo. `Product.price` solo cambia al editar el producto desde
> su propio formulario.

### Caso A — Creación

```python
self.product.stock -= self.quantity
self.cost = self.product.average_cost
self.product.save()
super().save(*args, **kwargs)
```

- Descuenta stock.
- Congela el costo (costo promedio al momento de la venta) en
  `self.cost`. Es histórico: no se recalcula al cambiar
  `Product.average_cost` después.
- `self.price` ya trae el valor que el usuario escribió en el form
  (por defecto `Product.price`, sugerido por AlpineJS al cambiar el
  selector de producto, pero **editable**). El modelo lo respeta
  tal cual.

### Caso B — Edición sin cambios reales (mismo producto y cantidad)

Solo `super().save()`. Cualquier cambio de precio que el usuario
haya hecho en el form se persiste (el form ya tiene el valor en
`self.price`).

### Caso C — Edición (cambia producto o cantidad)

Primero **revierte** devolviendo el stock viejo:

- **Producto diferente**: devuelve `quantity` al producto viejo,
  descuenta del producto nuevo y congela `cost` del nuevo
  (`new_prod.average_cost`).
- **Mismo producto**: aplica el delta neto
  (`stock += old.quantity - self.quantity`) sobre `old_prod` y
  congela `cost` (`old_prod.average_cost`).

En ambos casos, `self.price` **no se toca**: el valor que el usuario
escribió en el form se respeta. Esto es importante: si el usuario
cambia el producto de una línea y tenía un precio personalizado,
ese precio se mantiene (no se "resetea" al precio del nuevo
producto).

> Si permites vender más unidades de las que hay en stock, la resta
> dará negativo. No hay validación a nivel de modelo; revisa las
> plantillas (`invoice_form.html` muestra el stock actual por línea
> como hint, pero no bloquea).

---

## `Sale.delete()` — Borrar una línea

```python
self.product.stock += self.quantity
self.product.save()
super().delete(*args, **kwargs)
```

Simple: devuelve el stock al producto. No toca `average_cost` (es
esperable: las ventas no afectan el costo).

---

## Efectos colaterales importantes

### Borrar una factura (`PurchaseInvoice` / `SaleInvoice`)

`on_delete=CASCADE` desde `Purchase.invoice` y `Sale.invoice` hace que
Django borre las líneas. Cada línea ejecuta su `delete()`, revirtiendo
stock y (en compras) costo. **Borrar una factura es seguro.**

### Borrar un producto

`Purchase.product` y `Sale.product` están con `CASCADE`, así que borrar
un producto arrastra todas sus líneas. Cada línea ejecuta `delete()` y
revierte stock en productos que ya no existen (puede lanzar errores si
otros productos referenciaban al que se borra). En la práctica no se
recomienda borrar productos: usa `active=False` (soft-delete, ver
migración `0010_product_active`).

### Soft-delete (`Product.active`)

Introducido por la migración `0010`. Los productos inactivos:

- **No aparecen** en los formularios de facturas nuevas
  (`PurchaseItemForm` y `SaleItemForm` filtran por `active=True`).
- **No aparecen** en la API pública de productos
  (`stock/api.py` filtra por `active=True`).
- **Se excluyen** de las estadísticas y reportes del dashboard y
  vistas de reportes. Concretamente, las queries de `Sale` sobre
  ingresos, costos, top productos, top categorías, ventas por
  departamento y ventas por etiqueta añaden
  `product__active=True`. Las queries de `Product` sobre valor de
  inventario y alertas de stock (bajo / agotado) añaden
  `Product.active=True`.

  Esto significa que un producto inactivo:

  - No aporta al **valor de inventario** aunque conserve stock
    físico.
  - No genera alertas de stock bajo o agotado.
  - Sus ventas pasadas **dejan de contar** en estadísticas y
    reportes mientras esté inactivo. Si lo reactivas, vuelven a
    contar.

  Esta es la dirección natural del soft-delete: un producto
  descontinuado no es parte del catálogo actual. Si necesitas
  liquidar el stock restante, reactívalo temporalmente.

---

## Anulación y reactivación de facturas

> Para evitar que el inventario se desincronice por ediciones
> accidentales, las facturas (compra y venta) **no se pueden editar**
> en la UI. Para corregir una factura hay que **anularla** (revierte
> stock y costo) y crear una nueva. La anulación es **reversible**
> desde la misma UI, restaurando las líneas y reaplicando stock/costo.

### Anular una factura (`PurchaseInvoice.void()` / `SaleInvoice.void()`)

```python
def void(self, user, reason):
    if self.voided:
        return
    # 1) Snapshot de cada línea en VoidedInvoiceLine
    for item in self.items.all():
        VoidedInvoiceLine.objects.create(
            invoice_kind="purchase" if isinstance(self, PurchaseInvoice) else "sale",
            invoice_id=self.pk,
            product=item.product,
            quantity=item.quantity,
            unit_price=item.price if isinstance(self, SaleInvoice) else 0,
            unit_cost=item.cost if isinstance(self, PurchaseInvoice) else 0,
        )
    # 2) Borrar las líneas (item.delete() revierte stock/costo)
    for item in self.items.all():
        item.delete()
    # 3) Marcar factura como anulada
    self.voided = True
    self.voided_at = timezone.now()
    self.voided_by = user
    self.void_reason = reason
    self.save(update_fields=["voided", "voided_at", "voided_by", "void_reason"])
```

**Lo que ocurre al anular:**

- **Compras**: cada línea ejecuta `Purchase.delete()`, que revierte
  el stock y el costo promedio del producto (vía la fórmula
  simétrica a `update_average_cost`).
- **Ventas**: cada línea ejecuta `Sale.delete()`, que devuelve el
  stock al producto. El costo no se toca.
- Se guarda un snapshot de cada línea (producto, cantidad, precio o
  costo unitario) en `VoidedInvoiceLine` para permitir la
  reactivación.
- La factura queda marcada como `voided=True` con fecha, usuario y
  razón de la anulación.

La razón (`void_reason`) es **obligatoria**: la vista `void_*_invoice`
valida que llegue no vacía antes de ejecutar `void()`.

### Reactivar una factura (`PurchaseInvoice.reactivate()` / `SaleInvoice.reactivate()`)

```python
def reactivate(self):
    if not self.voided:
        return
    snapshots = VoidedInvoiceLine.objects.filter(
        invoice_kind="purchase" if isinstance(self, PurchaseInvoice) else "sale",
        invoice_id=self.pk,
    )
    for snap in snapshots:
        if isinstance(self, PurchaseInvoice):
            Purchase.objects.create(
                invoice=self, product=snap.product,
                quantity=snap.quantity, cost=snap.unit_cost,
            )
            # Purchase.save() reaplica stock y costo
        else:
            Sale.objects.create(
                invoice=self, product=snap.product,
                quantity=snap.quantity, price=snap.unit_price,
                cost=snap.product.average_cost,
            )
            # Sale.save() descuenta stock
    snapshots.delete()
    self.voided = False
    self.voided_at = None
    self.voided_by = None
    self.void_reason = ""
    self.save(update_fields=["voided", "voided_at", "voided_by", "void_reason"])
```

**Lo que ocurre al reactivar:**

- Lee las snapshots de `VoidedInvoiceLine` para esta factura.
- Recrea cada `Purchase` o `Sale` con los mismos datos guardados.
  Al persistirse, `Purchase.save()` / `Sale.save()` ejecutan su
  lógica de creación normal: re-suman stock (y recalculan
  `average_cost` para compras) o lo descuentan (para ventas).
- Borra las snapshots.
- Limpia los campos `voided*` de la factura.

> **Importante**: el `Sale.cost` que se graba al reactivar es
> `snap.product.average_cost` **actual** (no el del snapshot). Esto
> es coherente con el flujo de "crear venta nueva": el costo se
> congela al momento de la venta, y al reactivar una factura
> anulada, ese "momento" es ahora.

### Cómo se ve en la UI

- **Listas de facturas** (`/compras/`, `/ventas/`) muestran una
  columna **Estado** con "Activa" o "Anulada". La columna de
  acciones tiene:
  - **Activa**: botón "Anular" (icono `block`).
  - **Anulada**: botón "Reactivar" (icono `restore`).
  - En ambos casos: botón "Ver" (icono `visibility`) al detalle.
- **Detalle** (`/compras/<pk>/`, `/ventas/<pk>/`):
  - **Activa**: muestra los productos, sin banner. Botón
    "Anular" (icono `block`) que abre un `prompt()` JS pidiendo la
    razón. Si la razón está vacía, no se envía. Si es válida,
    ejecuta POST a `void_*_invoice`.
  - **Anulada**: muestra un banner rojo con fecha, usuario y razón
    de la anulación. Las líneas se siguen mostrando (siguen vivas
    en la base de datos al reactivarse). Botón "Reactivar" con
    `confirm()` JS.
- **Rutas `/compras/<pk>/edit/` y `/ventas/<pk>/edit/`**: devuelven
  `Http404`. Se conservan para que `reverse("purchase_invoice_edit")`
  no rompa en código viejo, pero la edición ya no existe.

### Efecto sobre los reportes y KPIs

Como `void()` borra las líneas (vía `delete()` que ejecuta la
reversión), todas las queries que suman `Sale.quantity * Sale.price`
(ingresos, top productos, ventas por departamento/etiqueta, estado
de resultados) **dejan automáticamente de contar** las ventas
anuladas. Lo mismo para los costos (`Sale.cost`) y para los
reportes de compras (que sumarían `Purchase.quantity * Purchase.cost`
pero esas líneas ya no existen).

No hace falta filtrar por `voided=False` en las queries: la
ausencia de líneas es suficiente.

### Integridad: el admin de Django

El admin de Django **sigue permitiendo** editar y borrar facturas.
Esto es intencional y el dueño del sistema es responsable de no
usar el admin para romper la integridad. La filosofía del cambio
es "no editar nunca" en la UI principal, pero se asume que el admin
lo usa el dueño con criterio.

---

## Cómo probar cambios en esta lógica

Sin tests automatizados (ver `arquitectura.md`), la verificación es
manual. Flujo sugerido:

1. Crea un producto `P` con stock 10 y costo promedio 5.
2. Compra 5 unidades a costo 7 → stock 15, promedio ponderado
   `(10·5 + 5·7) / 15 = 5.67`.
3. **Edita esa compra**: cambia cantidad a 3 → debería revertir
   `(15·5.67 - 5·7) / 10 = 4.0` stock 10, promedio 4.0; luego aplicar
   3 a 7 → `(10·4 + 3·7) / 13 ≈ 4.69`, stock 13.
4. Vende 4 unidades → stock 9, costo congelado en la línea.
5. Borra la venta → stock vuelve a 13.
6. Borra la compra → stock 10, promedio 5.

Si cualquiera de estos pasos no cuadra, hay un bug en la lógica.