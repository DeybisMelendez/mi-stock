# Importar y exportar datos

Mi Stock permite respaldar y restaurar la base de datos completa como
JSON desde la UI. Las vistas viven en `stock/views.py`
(`export_data`, `import_data`); los templates en
`templates/import_form.html`. Las URLs son `/exportar/` y
`/importar/`.

## Exportar

**Endpoint**: `GET /exportar/` (requiere login).
**Nombre de vista**: `export_data`.
**Nombre de URL**: `export_data`.

### Qué se exporta

Todos los registros de los siguientes modelos, en este orden:

```python
models_to_export = [
    "Category",
    "Tag",
    "ExpenseCategory",
    "Product",
    "ProductImage",
    "Department",
    "Customer",
    "PurchaseInvoice",
    "Purchase",
    "SaleInvoice",
    "Sale",
    "Expense",
    "OtherIncomeCategory",
    "OtherIncome",
]
```

> El orden importa para la importación: respeta las dependencias de FK.
> Categorías antes que productos, departamentos antes que clientes,
> facturas antes que líneas, etc.

### Formato del archivo

```json
{
  "metadata": {
    "export_date": "2026-08-19T15:30:00",
    "version": "1.3",
    "model_count": 14
  },
  "data": {
    "Category":       [ { "model": "stock.category", "pk": 1, "fields": { ... } }, ... ],
    "Tag":            [ ... ],
    "ExpenseCategory":[ ... ],
    "Product":        [ ... ],
    "ProductImage":   [ ... ],
    "Department":     [ ... ],
    "Customer":       [ ... ],
    "PurchaseInvoice":[ ... ],
    "Purchase":       [ ... ],
    "SaleInvoice":    [ ... ],
    "Sale":           [ ... ],
    "Expense":        [ ... ],
    "OtherIncomeCategory": [ ... ],
    "OtherIncome":    [ ... ]
  }
}
```

Cada entrada usa el formato estándar de
`django.core.serializers.serialize("json", queryset)`: un objeto por
instancia con `model`, `pk` y `fields`.

### Nombre del archivo

```
mi-stock-backup-YYYYMMDD-HHMMSS.json
```

Por ejemplo: `mi-stock-backup-20260819-153000.json`.

### Codificación

UTF-8 con `ensure_ascii=False`, indentado con 2 espacios. Apto para
leer y editar a mano si es necesario.

## Importar

**Endpoint**: `GET/POST /importar/` (requiere login).
**Nombre de vista**: `import_data`.
**Nombre de URL**: `import_data`.
**Template**: `import_form.html` con un `<input type="file" accept=".json">`.

### Flujo

1. GET → muestra el formulario.
2. POST con archivo → lee `request.FILES["backup_file"]`, decodifica
   UTF-8 y hace `json.loads`.
3. Itera sobre los modelos en el mismo orden de exportación.
4. Para cada modelo, usa `serializers.deserialize("json", ...)` y
   llama a `obj.save()` en cada uno.
5. Muestra `messages.success` con el conteo por modelo.

### Comportamiento importante: **sobrescribe por PK**

`serializers.deserialize` con `save()` aplica las instancias a la base
de datos usando los PKs del JSON. Esto significa que:

- Si un PK ya existe en la BD, **se actualiza** (no se duplica).
- Si un PK no existe, **se crea**.
- **No hay merge**: el archivo es la fuente de verdad.

### Advertencias

- ⚠️ **No hay dry-run**. La importación modifica la BD inmediatamente.
- ⚠️ **Hace un backup antes** (manual, desde `/exportar/`).
- ⚠️ **Las fotos no se incluyen**: `ProductImage.image` es una ruta al
  archivo en `MEDIA_ROOT`. El JSON guarda la ruta, pero los archivos
  físicos deben respaldarse por separado (carpeta `media/`).
- ⚠️ **El contador de stock no se recalcula**: si importas sobre una BD
  con stocks divergentes, los datos importados (que incluyen
  `Product.stock` y `Product.average_cost`) prevalecen.
- ⚠️ **No valida dependencias**: si el JSON está corrupto o le faltan
  modelos previos, las FKs apuntarán a PKs inexistentes y la
  importación fallará en mitad del proceso (los modelos previos a la
  falla ya quedaron guardados).

## Cómo hacer un ciclo completo

```bash
# 1. Asegúrate de tener la BD actual en buen estado
python manage.py check

# 2. Exporta desde la UI (o por shell):
python manage.py shell -c "
from stock.views import export_data
from django.test import RequestFactory
req = RequestFactory().get('/exportar/')
req.user = ... # usuario autenticado
print(export_data(req).content.decode())
" > backup.json

# 3. Restaura sobre una BD limpia:
rm db.sqlite3
python manage.py migrate
# Login como superusuario y subir backup.json desde /importar/
```

## Añadir un modelo al export/import

1. Modelo en `stock/models.py`.
2. Migración (`makemigrations` + `migrate`).
3. **Añadir a `models_to_export`** en `views.py:export_data` (orden
   importa — modelos referenciados antes que los que los referencian).
4. **Añadir al mismo orden** en `import_data.models_order`.
5. Documentar el cambio en
   [`docs/mantenimiento.md`](mantenimiento.md).
6. Considerar actualizar la `version` en `metadata` si el cambio rompe
   compatibilidad con backups antiguos.

## Riesgos y limitaciones

| Riesgo | Mitigación |
|---|---|
| Sobrescritura accidental | Backup antes; verificar contenido del JSON |
| Falta de fotos tras restaurar | Respaldar también `media/` (carpeta física) |
| Stock inconsistente tras importar | Exportar e importar **la misma BD**; no mezclar |
| Importación parcial si falla a mitad | Validar JSON antes; FKs completas en orden |
| Schema drift entre versiones | Mantener `metadata.version` actualizado |