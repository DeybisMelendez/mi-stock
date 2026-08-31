# Formularios

Definidos en `stock/forms.py`. Son `ModelForm` simples más un `inlineformset_factory`
para las fotos de productos. **Los formsets de líneas de factura
(`PurchaseItemFormSet`, `SaleItemFormSet`) están en `views.py`, no aquí.**

## Forms simples

| Form | Modelo | Campos |
|---|---|---|
| `CategoryForm` | `Category` | `name` |
| `ExpenseCategoryForm` | `ExpenseCategory` | `name` |
| `OtherIncomeCategoryForm` | `OtherIncomeCategory` | `name` |
| `ProductForm` | `Product` | `name`, `category`, `brand`, `description`, `stock`, `price`, `average_cost`, `active` |
| `ExpenseForm` | `Expense` | `date`, `category`, `amount`, `description` |
| `OtherIncomeForm` | `OtherIncome` | `date`, `category`, `amount`, `description` |
| `CustomerForm` | `Customer` | `name`, `whatsapp`, `address`, `department`, `notes`, `active` |

Los forms de fecha (`ExpenseForm`, `OtherIncomeForm`) usan un widget HTML5:

```python
widgets = {
    "date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
}
```

> El campo `ProductForm.stock` es editable directamente. Úsalo solo para
> ajustes manuales; el flujo normal es crear compras, que actualizan el
> stock automáticamente vía `Purchase.save()`.

## ProductForm + formset de fotos

`ProductForm` se complementa con `ProductImageFormSet` para gestionar
múltiples fotos de un producto:

```python
ProductImageFormSet = forms.inlineformset_factory(
    Product, ProductImage,
    fields=["image"],
    extra=1, can_delete=True,
)
```

- `extra=1` muestra una fila vacía por defecto.
- `can_delete=True` permite marcar fotos para eliminar.

La vista `product_form_view` (`stock/views.py`) los combina: valida
ambos, guarda el producto, asigna `formset.instance = product` y
guarda el formset.

## Forms de facturas

`PurchaseInvoiceForm` y `SaleInvoiceForm` son `ModelForm` simples con
solo la cabecera:

| Form | Modelo | Campos | Widget |
|---|---|---|---|
| `PurchaseInvoiceForm` | `PurchaseInvoice` | `date`, `supplier` | `date` como `type="date"` |
| `SaleInvoiceForm` | `SaleInvoice` | `date`, `customer_obj` | `date` como `type="date"` |

`SaleInvoiceForm` tiene solo `customer_obj` (FK a `Customer`, obligatorio)
y limita el queryset a clientes activos. No hay campo de texto libre
para cliente: si el cliente no está registrado, hay que crearlo desde
el CRUD de clientes (enlazado desde el formulario de venta).

### `CustomerForm`

```python
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "whatsapp", "address", "department", "notes", "active"]
        widgets = {
            "whatsapp": forms.TextInput(attrs={"type": "tel", "placeholder": "+505 8888 8888"}),
        }
```

Se usa en el CRUD genérico (`generic_form_view` con `model_str="customer"`).
No tiene validación rígida del whatsapp (Nicaragua usa `+505` + 8 dígitos,
pero no queremos romper entradas con prefijos de otros países).

### `PurchaseItemForm`

```python
class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ["product", "quantity", "cost"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(active=True)
```

- Limita el selector de producto a los **activos**. Esto implementa
  el soft-delete a nivel de formulario (ver
  [`migraciones.md`](migraciones.md) `0010_product_active`).

### `SaleItemForm`

Igual idea, pero sin campo `cost` (lo llena `Sale.save()`):

```python
class SaleItemForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["product", "quantity"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(active=True)
```

## Formsets de líneas (definidos en `views.py`)

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

- `extra=1` → una fila vacía inicial.
- `can_delete=True` → cada línea puede marcarse para borrar al guardar
  la factura.

Las vistas `purchase_invoice_form_view` y `sale_invoice_form_view`
manejan `POST` con esta secuencia:

1. `form = InvoiceForm(request.POST, instance=invoice)`
2. `formset = InvoiceItemFormSet(request.POST, instance=invoice)`
3. Si ambos válidos → `form.save()` y luego
   `formset.instance = invoice; formset.save()`.
4. `redirect("purchase_invoice_new")` o `sale_invoice_new`.

## Cómo añadir un campo a un form existente

1. Añade el campo al modelo en `stock/models.py`.
2. Crea la migración con `python manage.py makemigrations stock`.
3. Aplica con `python manage.py migrate`.
4. Añade el campo a `Meta.fields` del form correspondiente en
   `stock/forms.py`.
5. **Si el campo debe renderizarse en `list.html`** (Grid.js), sigue
   las instrucciones de
   [`docs/mantenimiento.md`](mantenimiento.md#nuevo-campo-en-un-modelo-existente).
6. **Si quieres widgets personalizados**, usa `Meta.widgets` igual que
   en `ExpenseForm`.

## Cómo añadir un form nuevo

1. Modelo en `stock/models.py` + migración.
2. `ModelForm` en `stock/forms.py`.
3. Decide si va por el CRUD genérico o por una vista dedicada.
   - **Genérico**: añade el `case` en `generic_list_view` y
     `generic_form_view`, extiende los `valid_models`, y la URL en
     `stock/urls.py`. Detalles en
     [`docs/vistas-y-urls.md`](vistas-y-urls.md#añadir-un-nuevo-modelo-crud-simple).
   - **Dedicado**: crea una vista en `views.py` y rutas explícitas en
     `urls.py`.
4. Si el form es complejo (formset, AJAX, lógica custom), crea un
   template propio y referéncialo en la vista.
5. Documenta el cambio.