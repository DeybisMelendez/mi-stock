# Migraciones

Listado y notas de las migraciones en `stock/migrations/`. La base de
datos es SQLite (`db.sqlite3` en la raíz). **Los archivos `db.bak.sqlite3`,
`db.bak2.sqlite3` y `db.bak3.sqlite3` son backups manuales** — no los
gestiona Django.

## Listado cronológico

| # | Archivo | Qué hace |
|---|---|---|
| 0001 | `0001_initial.py` | Modelos iniciales: `Category`, `Product`, `Purchase`, `Sale` |
| 0002 | `0002_product_average_cost_purchase_created_at_sale_cost_and_more.py` | Añade `average_cost` a `Product`, `created_at` a `Purchase`, `cost` a `Sale`, y la tabla `Expense` |
| 0003 | `0003_expense_alter_purchase_date_alter_purchase_supplier_and_more.py` | Ajustes a `Expense`, `Purchase.date`, `Purchase.supplier` |
| **0004** | `0004_invoices_add_models.py` | Crea `PurchaseInvoice` y `SaleInvoice` (con `date` aún como `DateTimeField`); añade FK `invoice` (nullable) a `Purchase` y `Sale`; ordena `Expense` por `-created_at` |
| **0005** | `0005_invoices_backfill.py` | **Migración de datos**: agrupa `Purchase`/`Sale` por día, crea una factura por día con el proveedor/cliente más frecuente y las enlaza |
| **0006** | `0006_invoices_drop_line_fields.py` | Elimina `date` y `supplier` de `Purchase` y `customer` y `date` de `Sale`; convierte `invoice` FK en no-nullable |
| 0007 | `0007_expensecategory_product_brand_alter_expense_date_and_more.py` | Crea `ExpenseCategory`, añade `brand` a `Product`, altera campos de `Expense` |
| 0008 | `0008_truncate_dates_to_date.py` | Convierte `invoice.date` de `DateTimeField` a `DateField` (truncando la hora) |
| 0009 | `0009_otherincomecategory_otherincome.py` | Crea `OtherIncomeCategory` y `OtherIncome` |
| 0010 | `0010_product_active.py` | Añade `Product.active` (BooleanField, default `True`) — soft-delete |

## ⚠️ Bloque 0004–0006: NO son reversibles sobre datos reales

Las migraciones `0004_invoices_add_models.py`, `0005_invoices_backfill.py`
y `0006_invoices_drop_line_fields.py` realizan un **reshape** del modelo
de datos (separar factura + línea) y luego **eliminan campos** que ya no
son necesarios (`Purchase.date`, `Purchase.supplier`, `Sale.date`,
`Sale.customer`).

### Por qué no revertirlas

- `0005` hace una **migración de datos** que agrupa por día y elige un
  proveedor/cliente. Al revertir (`remove_invoices`), se pierde esa
  información.
- `0006` **borra campos** del esquema. Revertir los recrea como vacíos.
  Toda la información histórica de fechas y partes (que ahora vive en
  la cabecera de la factura) se pierde.

### Qué hacer si necesitas volver atrás

**No** uses `migrate stock 0003`. Restaura desde un backup:

```bash
cp db.bak.sqlite3 db.sqlite3  # o el backup más reciente
python manage.py migrate  # reaplica 0004+ sobre la base restaurada si aplica
```

## Otras migraciones con reshape

- **`0008_truncate_dates_to_date.py`**: convierte el campo `date` de
  `DateTimeField` a `DateField`. La parte de hora de los datos
  existentes se trunca. Si necesitas mantener horas, revisa el código
  de la migración antes de aplicarla sobre datos reales.

## Buenas prácticas al migrar

1. **Backup antes de migrar**. Especialmente en producción o con datos
   reales:

   ```bash
   cp db.sqlite3 db.sqlite3.bak-$(date +%Y%m%d-%H%M%S)
   python manage.py migrate
   ```

2. **No edites migraciones ya aplicadas** salvo que sean recientes y
   aún no estén en producción. Si necesitas cambiar una migración
   aplicada: crea una nueva, no reescribas la historia.

3. **No hagas `squashmigrations` sobre `0004–0006`**: las migraciones
   de datos no se pueden fusionar limpiamente.

4. **Después de migrar**, verifica que las vistas siguen funcionando:
   inventario coherente, facturas con totales correctos, etc.

## Comandos frecuentes

```bash
python manage.py makemigrations stock   # crear migración desde cambios en modelos
python manage.py migrate                # aplicar todas las pendientes
python manage.py showmigrations         # ver estado
python manage.py sqlmigrate stock NNNN  # ver SQL de una migración
python manage.py migrate stock 0003     # revertir hasta 0003 (¡no usar si 0004+ tiene datos!)
```

## Backups manuales

En la raíz hay varios `db.bak.sqlite3`:

- `db.bak.sqlite3`
- `db.bak2.sqlite3`
- `db.bak3.sqlite3`

Estos snapshots se hicieron manualmente y **no siguen ningún esquema
formal** (puede que les falten migraciones aplicadas si se restauran
directamente). Antes de usar uno como base activa, asegúrate de que el
número de migraciones aplicadas en la tabla `django_migrations` coincide
con el estado de los modelos. Si no, aplica con
`python manage.py migrate` (es seguro si no introduces nuevas
migraciones de datos en producción).