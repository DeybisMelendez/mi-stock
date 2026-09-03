# Arquitectura

Este documento describe la estructura general del proyecto Mi Stock: sus
componentes, el stack tecnológico y cómo se conectan las piezas.

## Vista general

Mi Stock es una aplicación Django 5 monolítica de un solo proceso, pensada
para uso personal o pequeños negocios. Toda la lógica vive en una única app
(`stock`); el paquete `mistock/` es solo configuración de proyecto.

```
┌─────────────────────────────────────────────────────────────┐
│                       Navegador (cliente)                    │
│            Pico CSS + Material Icons (CDN)                   │
│            AlpineJS + Chart.js + Grid.js (CDN)               │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Django (mistock/)                        │
│  ┌──────────────────────┐    ┌──────────────────────────┐   │
│  │  URL routing         │───▶│  Vistas (stock/views.py) │   │
│  │  (mistock/urls.py)   │    │  - @login_required       │   │
│  │  (stock/urls.py)     │    │  - Vistas dedicadas      │   │
│  └──────────────────────┘    └──────────┬───────────────┘   │
│                                         │                    │
│                                         ▼                    │
│                          ┌──────────────────────────────┐    │
│                          │  Modelos (stock/models.py)   │    │
│                          │  - save()/delete() mutan     │    │
│                          │    Product.stock/cost        │    │
│                          └──────────┬───────────────────┘    │
└─────────────────────────────────────┼─────────────────────────┘
                                      ▼
                              ┌───────────────┐
                              │  SQLite       │
                              │  db.sqlite3   │
                              └───────────────┘
```

## Estructura de carpetas

```
.
├── manage.py
├── mistock/                  # Configuración de proyecto
│   ├── settings.py           # Lee .secret, INSTALLED_APPS, etc.
│   ├── urls.py               # admin, /accounts/, include('stock.urls')
│   ├── wsgi.py / asgi.py     # Despliegue
│
├── stock/                    # App única con toda la lógica
│   ├── models.py             # 10 modelos del dominio
│   ├── views.py              # Vistas + PurchaseItemFormSet / SaleItemFormSet
│   ├── forms.py              # ModelForms y formsets
│   ├── api.py                # API pública de productos (solo lectura)
│   ├── urls.py               # Rutas (path() explícitos por modelo)
│   ├── admin.py              # Registro en Django admin
│   ├── apps.py
│   ├── templatetags/
│   │   └── getattribute.py   # Filtro `markdown_safe`
│   ├── migrations/           # 15 migraciones (0001 → 0015)
│   └── tests.py              # Vacío (no hay suite)
│
├── templates/                # Plantillas a nivel de proyecto
│   ├── layout.html           # Layout base con navbar y CDN
│   ├── includes/             # Parciales: grid_table, tag_filter,
│   │                         # period_nav, messages
│   ├── <m>_list.html         # Lista por modelo (category, tag,
│   │                         # customer, product, purchase, sale...)
│   ├── <m>_form.html         # Form por modelo (category, tag,
│   │                         # customer, expense...)
│   ├── product_form.html     # Producto + formset de fotos
│   ├── invoice_form.html     # Factura compra/venta + formset + subtotales
│   ├── product_detail.html   # Detalle de producto (galería)
│   ├── invoice_detail.html   # Detalle de factura
│   ├── home.html             # Dashboard con KPIs y Chart.js
│   ├── month_result.html     # Estado de resultados mensual
│   ├── user_profile.html     # Perfil de usuario
│   ├── import_form.html      # Subida de archivo de respaldo
│   └── registration/
│       └── login.html        # Login estándar
│
├── static/css/styles.css     # Hoja de estilos de la app
├── docs/                     # Esta documentación
├── AGENTS.md                 # Convenciones operativas para agentes
└── README.md
```

## Stack tecnológico

### Backend

- **Python 3.x**
- **Django 5.2.7** (ver `requirements.txt`)
- **SQLite** como base de datos por defecto (configurada en
  `mistock/settings.py`)
- **Pillow 11.x** para `ImageField` de `ProductImage`
- **markdown** + **bleach** para renderizar la descripción markdown de
  productos de forma segura (filtro `markdown_safe` en plantillas)
- **python-dotenv** para cargar `.secret`
- **django-cors-headers 4.x** para el CORS de la API pública
  (solo rutas `/api/...`, ver [`api.md`](api.md))

No hay servidor de producción configurado: solo `runserver` para desarrollo.

### Frontend (todo por CDN, sin build step)

- **[Pico CSS 2.x](https://picocss.com/)** — base del estilo, tema naranja
  cargado desde CDN.
- **[Material Icons](https://fonts.google.com/icons)** — iconografía.
- **[AlpineJS](https://alpinejs.dev/)** — reactividad ligera
  (tabs, subtotales de facturas, mensajes descartables, galería de fotos).
- **[Chart.js](https://www.chartjs.org/)** — gráficos del dashboard
  (`home.html`), cargado solo en esa página.
- **[Grid.js](https://gridjs.io/)** — tablas con búsqueda y paginación
  (parcial `includes/grid_table.html`, incluido por los templates de
  lista y reportes).

**No hay**:

- `static/` con assets a compilar (no hay npm/webpack/vite).
- `package.json`.
- Pipelines de build para frontend.

Si necesitas CSS, va en `static/css/styles.css`. Ver
[`docs/estilos.md`](estilos.md).

### Internacionalización

- `LANGUAGE_CODE = 'es-ni'` (español de Nicaragua)
- `TIME_ZONE = 'America/Managua'`
- `USE_I18N = True`, `USE_TZ = True`

Todos los textos visibles al usuario están en español.

## Capas de la aplicación

### 1. Configuración (`mistock/`)

`mistock/settings.py` carga variables desde `.secret` con
`load_dotenv(dotenv_path=".secret")`. Las claves relevantes son:

- `DJANGO_SECRET_KEY` — clave secreta de Django.
- `DJANGO_DEBUG` — activa modo debug solo si el valor es exactamente `True`.

`mistock/urls.py` monta:

- `admin/` → `django.contrib.admin`
- `accounts/` → `django.contrib.auth.urls` (login, logout, password reset)
- `""` → `include("stock.urls")`

En `DEBUG=True`, sirve también archivos de `MEDIA_URL`.

### 2. Routing (`stock/urls.py`)

Define rutas explícitas con `path()` para todas las vistas: cada
modelo simple tiene su lista, su formulario y sus tres rutas propias
(`/m/`, `/m/new/`, `/m/<pk>/edit/`). No hay vistas genéricas ni
regex. Detalles en [`vistas-y-urls.md`](vistas-y-urls.md).

### 3. Vistas (`stock/views.py`)

Todas llevan `@login_required` y son funciones dedicadas: cada vista
renderiza su propio template.

- **CRUD por modelo**: `<m>_list_view` y `<m>_form_view` para los 7
  modelos simples, más `product_list_view`, `purchase_list_view` y
  `sale_list_view`.
- **Vistas complejas**: `product_form_view`, `product_detail_view`,
  `purchase_invoice_form_view`, `sale_invoice_form_view`, `month_result`,
  `top_products_view`, `export_data`, `import_data`, `user_profile`,
  `purchase_invoice_detail_view`, `sale_invoice_detail_view`.

Los formsets inline `PurchaseItemFormSet` y `SaleItemFormSet` se construyen
aquí con `inlineformset_factory`, **no** en `forms.py`.

> La **API pública** de productos no vive aquí: está en `stock/api.py`,
> sin login y de solo lectura. Ver [`api.md`](api.md).

### 4. Modelos (`stock/models.py`)

10 modelos del dominio. Lo más delicado es que `Purchase.save()`,
`Purchase.delete()`, `Sale.save()` y `Sale.delete()` **mutan** el stock y
el costo promedio de `Product`. Detalles en
[`logica-stock-costo.md`](logica-stock-costo.md).

### 5. Forms (`stock/forms.py`)

ModelForms por modelo + `ProductImageFormSet`. Los formsets de facturas
están en `views.py`. Detalles en [`formularios.md`](formularios.md).

### 6. Plantillas

Todas viven en `templates/` (no hay `stock/templates/`). `layout.html`
provee la barra de navegación con dropdown agrupado (Catálogo /
Operaciones / Reportes / Cuenta / Datos) y carga todos los CDN.

Detalle en [`frontend.md`](frontend.md).

### 7. Estilos

Una sola hoja: `static/css/styles.css`. Convenciones BEM-light, tokens
propios `--ms-*` que derivan de variables de Pico, sin `style=""` ni
`<style>` en templates. Ver [`docs/estilos.md`](estilos.md).

## Flujo de un request típico

1. El usuario navega (p. ej. a `/product/`).
2. `mistock/urls.py` → `include("stock.urls")` → `path()` matchea
   `product/` → `views.product_list_view(request)`.
3. La vista consulta los productos y serializa cada fila a JSON
   (`headers_json` + `data_json`, con la celda de acciones como objeto).
4. Renderiza `templates/product_list.html` con el contexto.
5. En el navegador, el parcial `includes/grid_table.html` monta Grid.js
   con búsqueda y paginación, y AlpineJS activa los tabs.

## Lo que NO está en el proyecto

- **Sin API REST autenticada ni de escritura**: la única API es la
  pública de productos, de solo lectura (ver [`api.md`](api.md)).
  Todo lo demás es HTML server-rendered.
- **Sin tareas asíncronas** (no hay Celery, no hay cron).
- **Sin tests** (`tests.py` está vacío).
- **Sin CI / lint / formatter** configurados.
- **Sin Docker / docker-compose**.
- **Sin servidor de producción** (Gunicorn, Nginx, etc. no están
  configurados).

Si vas a añadir cualquiera de estos, actualiza los docs correspondientes
según [`mantenimiento.md`](mantenimiento.md).