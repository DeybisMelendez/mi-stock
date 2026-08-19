# AGENTS.md

Django 5 inventory app (`mi-stock`). Single real app is `stock`; `mistock/` is the project package (settings, urls, wsgi/asgi). All business logic, models, views, and forms live in `stock/`.

## Estilo de código

- Programar en inglés siempre, pero comentarios y documentación en español.
- Programar de manera simple, legible, fácil de leer y comprender, sin complicaciones.
- Buscar siempre la solución más simple y sencilla.

## Environment & setup

- The Python virtualenv is the directory literally named `.env/` (activate with `source .env/bin/activate`). It is gitignored. Despite the name, it is NOT an env-var file.
- Real env vars live in `.secret` at the repo root (also gitignored), loaded via `load_dotenv(dotenv_path=".secret")` in `mistock/settings.py`. Keys: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`. A working `.secret` is required to run the server; `DEBUG` is only on when the value is exactly the string `True`.
- Install deps: `pip install -r requirements.txt` inside the venv. `requirements.txt` is minimal and not pinned beyond Django 5.2.7.
- DB is SQLite at `db.sqlite3` (root, gitignored). `db.bak.sqlite3` / `db.bak2.sqlite3` are manual backups, not managed by migrations.

## Commands

```bash
python manage.py runserver              # dev server
python manage.py makemigrations stock   # after model changes
python manage.py migrate
python manage.py createsuperuser        # needed to log in (all views are @login_required)
python manage.py test                   # NOTE: stock/tests.py is empty; there is effectively no test suite
```

There is no lint/typecheck/formatter config in the repo. CI: none.

## Migrations — read before touching

`stock/migrations/0004_invoices_add_models.py`, `0005_invoices_backfill.py`, and `0006_invoices_drop_line_fields.py` perform a data-migration reshape (invoice/line item split) and then drop old fields. They are **not safely reversible**. Do not re-squash or roll back across 0004–0006 on a DB with real data; re-run from a backup instead.

## Architecture notes worth knowing

- **Stock/cost logic lives in model `save()`/`delete()` overrides**, not in views or signals. `Purchase.save` and `Sale.save` mutate `Product.stock` and `Product.average_cost` (average-cost accounting), and carefully revert old values when editing. Any change to these flows must preserve the revert-then-apply logic or the inventory will drift. See `stock/models.py`.
- **Generic views by model string**: `stock/urls.py` routes `category|product|sale|purchase|expense` through one `generic_list_view` / `generic_form_view` keyed by `model_str`. Add new simple CRUD models by extending that regex set and the associated `apps.get_model` map, not by writing per-model views.
- **Invoices use inline formsets**: `purchase_invoice_form_view` / `sale_invoice_form_view` build `PurchaseItemFormSet` / `SaleItemFormSet` via `inlineformset_factory`. Edit both the invoice form and the item formset together.
- **All views are `@login_required`**. Auth URLs live at `/accounts/` via `django.contrib.auth.urls`; `LOGIN_REDIRECT_URL = '/'`.
- URL slugs are in Spanish (`compras/`, `ventas/`, `resultados/`, `exportar/`, `importar/`). Locale is `es-ni`, timezone `America/Managua`.
- Templates: project-level at `templates/` (not per-app). Frontend is Pico CSS + AlpineJS via CDN, no JS build step and no `static/` source assets to compile.

## Templates convention

`stock/templatetags/getattribute.py` provides a `getattribute` filter used to dynamic-attribute access in the generic list/form templates — keep it in mind when adding fields to models that the generic templates render by name.

## Documentation

- Toda la documentación técnica del proyecto vive en `docs/`. El índice está en `docs/README.md` y cubre arquitectura, modelos, vistas/URLs, formularios, lógica de stock/costo, migraciones, import/export, autenticación, frontend y mantenimiento de docs.
- `opencode.json` ya carga `docs/*.md` y `README.md` como instrucciones, así que el contenido de `docs/` forma parte del contexto de futuros agentes automáticamente.
- **Regla obligatoria**: cualquier cambio de funcionalidad debe ir acompañado de la actualización de los archivos de `docs/` correspondientes. El checklist concreto está en `docs/mantenimiento.md`. Si el cambio toca `Purchase`/`Sale.save()|delete()`, **es obligatorio** actualizar `docs/logica-stock-costo.md`.