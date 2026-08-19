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

### Caso A — Creación

```python
self.product.stock -= self.quantity
self.price = self.product.price
self.cost = self.product.average_cost
self.product.save()
super().save(*args, **kwargs)
```

- Descuenta stock.
- Congela precio y costo al estado actual del producto.

### Caso B — Edición sin cambios reales (mismo producto y cantidad)

Solo `super().save()`.

### Caso C — Edición (cambia producto o cantidad)

Primero **revierte** devolviendo el stock viejo:

- **Producto diferente**: devuelve `quantity` al producto viejo,
  descuenta del producto nuevo y congela precio/costo del nuevo.
- **Mismo producto**: aplica el delta neto
  (`stock += old.quantity - self.quantity`) sobre `old_prod` y congela
  precio/costo.

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

- Siguen contando para el dashboard y reportes históricos.
- **No aparecen** en los formularios de facturas nuevas
  (`PurchaseItemForm` y `SaleItemForm` filtran por `active=True`).

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