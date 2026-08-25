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
│  │  (stock/urls.py)     │    │  - CRUD genérico + ded.  │   │
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
│   ├── urls.py               # Rutas (con regex para CRUD genérico)
│   ├── admin.py              # Registro en Django admin
│   ├── apps.py
│   ├── templatetags/
│   │   └── getattribute.py   # Filtros `getattribute` y `format_value`
│   ├── migrations/           # 10 migraciones (0001 → 0010)
│   └── tests.py              # Vacío (no hay suite)
│
├── templates/                # Plantillas a nivel de proyecto
│   ├── layout.html           # Layout base con navbar y CDN
│   ├── list.html             # Lista con Grid.js + Alpine (tabs en productos)
│   ├── form.html             # Formulario genérico
│   ├── product_form.html     # Producto + formset de fotos
│   ├── invoice_form.html     # Factura compra/venta + formset + subtotales
│   ├── product_detail.html   # Detalle de producto (galería)
│   ├── invoice_detail.html   # Detalle de factura
│   ├── home.html             # Dashboard con KPIs y Chart.js
│   ├── month_result.html     # Estado de resultados mensual
│   ├── user_profile.html     # Perfil de usuario
│   ├── import_form.html      # Subida de archivo de respaldo
│   ├── includes/
│   │   └── messages.html     # Mensajes Django con cierre Alpine
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
  (`list.html`).

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

Define rutas explícitas para vistas dedicadas (`home`, facturas, producto)
y usa `re_path` con regex para mapear el CRUD genérico por nombre de modelo
(`category`, `product`, `sale`, `purchase`, etc.). Detalles en
[`vistas-y-urls.md`](vistas-y-urls.md).

### 3. Vistas (`stock/views.py`)

Todas llevan `@login_required`. Hay dos estilos:

- **CRUD genérico**: `generic_list_view` y `generic_form_view` resuelven
  el modelo a partir de un `model_str` y un mapeo `MODEL_NAME_MAP`.
- **Vistas dedicadas**: `home`, `product_form_view`, `product_detail_view`,
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
2. `mistock/urls.py` → `include("stock.urls")` → `re_path` matchea
   `product` → `views.generic_list_view(request, model_str="product")`.
3. La vista valida que `model_str` esté en `valid_models`, resuelve el
   modelo con `apps.get_model("stock", "PurchaseInvoice")` (mapeo via
   `MODEL_NAME_MAP`) y prepara los datos según el caso.
4. Serializa los productos a JSON para alimentar Grid.js en el cliente.
5. Renderiza `templates/list.html` con el contexto.
6. En el navegador, AlpineJS activa los tabs y Grid.js monta la tabla
   con búsqueda y paginación.

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