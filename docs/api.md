# API pública de productos

API REST de **solo lectura** que expone el catálogo de productos
disponibles. No requiere autenticación. El código vive en
`stock/api.py` (vistas `api_product_list` y `api_product_detail`);
las rutas están en `stock/urls.py`.

> **Doc pública**: existe además una guía para **consumidores** de la
> API en [`API.md`](../API.md) (raíz del repo, junto al README). Ese
> archivo no documenta internals; si cambias endpoints o formato,
> actualízalo también.

## Endpoints

| Método | URL | Nombre | Descripción |
|---|---|---|---|
| GET | `/api/products/` | `api_product_list` | Lista de productos disponibles |
| GET | `/api/products/<pk>/` | `api_product_detail` | Detalle de un producto |

- Cualquier otro método (POST, PUT, DELETE…) devuelve **405 Method Not
  Allowed** (`require_GET`). Las vistas llevan además `csrf_exempt`
  para que el 405 sea determinista (sin ella, el middleware CSRF
  respondería 403 primero en POST/PUT). Es seguro: las vistas solo
  soportan GET, no hay estado que proteger.
- No hay endpoint de creación, edición ni borrado: la gestión sigue
  siendo por la UI autenticada.
- No requiere login (son las únicas vistas públicas del proyecto).

## Qué es un "producto disponible"

`active=True`. Esto incluye tanto productos con existencias como
productos agotados (`stock=0`). Los productos inactivos
(soft-delete) son los únicos excluidos.

Para distinguir disponibilidad de stock sin exponer la cantidad, el
payload incluye el campo booleano `in_stock` (`true` si hay
existencias, `false` si está agotado). Ver "Campos excluidos a
propósito" más abajo.

El detalle de un producto inactivo o inexistente devuelve **404** con
body JSON (`{"error": "Producto no encontrado."}`), sin distinguir
entre "no existe" e "inactivo" (para no filtrar información por ID).

## Formato de respuesta

Lista (`GET /api/products/`):

```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "Coca-Cola 600ml",
      "description": "Bebida gaseosa",
      "price": "25.00",
      "in_stock": true,
      "category": {"id": 2, "name": "Bebidas"},
      "tags": ["oferta", "nuevo"],
      "images": ["https://mi-stock-alphatechni.pythonanywhere.com/media/product_images/foto1.jpg"]
    },
    {
      "id": 5,
      "name": "Mouse inalámbrico",
      "description": "",
      "price": "350.00",
      "in_stock": false,
      "category": {"id": 3, "name": "Accesorios"},
      "tags": [],
      "images": []
    }
  ]
}
```

Detalle (`GET /api/products/1/`): el mismo objeto, sin envoltorio.

Notas del formato:

- **`price` es string** (p. ej. `"25.00"`). Es la serialización directa
  del `DecimalField`; evita problemas de precisión flotante en el
  consumidor.
- **`in_stock` es boolean** derivado de `Product.stock > 0` al momento
  de la consulta. Permite al consumidor distinguir productos con
  existencias de los agotados **sin** revelar la cantidad exacta en
  inventario.
- **`description`** se envía como **markdown plano** (string sin
  procesar). El consumidor es responsable de renderizarlo si lo desea.
  La UI interna de Mi Stock lo renderiza con el filtro `markdown_safe`
  (ver [`docs/frontend.md`](frontend.md)).
- **`images`** es una lista de URLs **absolutas** (con esquema y host,
  construidas con `request.build_absolute_uri`). Si un producto no
  tiene fotos, es `[]`.
- **`category`** es un objeto `{id, name}`.
- **`tags`** es una lista de strings (nombres de etiqueta). Si un
  producto no tiene etiquetas, es `[]`. Lista ordenada por el
  `Meta.ordering` de `Tag` (`name`).
- No hay paginación: el catálogo es pequeño y la respuesta completa
  es la solución más simple.
- Orden: el `Meta.ordering` de `Product` (`name`, `category__name`).

## Campos excluidos a propósito

- `average_cost` — costo interno del negocio. **Nunca** debe exponerse.
- `stock` — cantidad en inventario (interno del negocio).

Por eso `_product_payload` en `stock/api.py` usa una **whitelist
explícita** de campos en lugar de serializar el modelo completo: si
se añade un campo público nuevo, hay que añadirlo a mano al payload
(y documentarlo aquí); cualquier campo no listado queda fuera por
defecto.

## CORS

La API se puede consumir desde cualquier origen (navegador incluido).
Configuración en `mistock/settings.py`:

```python
CORS_ALLOW_ALL_ORIGINS = True
CORS_URLS_REGEX = r"^/api/.*$"
```

- `django-cors-headers` (en `INSTALLED_APPS` y `MIDDLEWARE`) envía
  `Access-Control-Allow-Origin: *` **solo** en rutas `/api/...`.
- No se envía `Access-Control-Allow-Credentials`, por lo que las
  cookies de sesión **no** viajan cross-origin: el resto de la app
  (protegida por login) no queda expuesto por el CORS.

## Ejemplos

```bash
# Lista
curl https://mi-stock-alphatechni.pythonanywhere.com/api/products/

# Detalle
curl https://mi-stock-alphatechni.pythonanywhere.com/api/products/1/

# Método no permitido (405)
curl -X POST https://mi-stock-alphatechni.pythonanywhere.com/api/products/
```

## Advertencia sobre producción

En desarrollo (`DEBUG=True`) Django sirve los archivos de `media/`.
En producción, si el servidor web (Nginx, etc.) no sirve `MEDIA_URL`,
las URLs de `images` devolverán 404. Asegúrate de servir `/media/`
además de `/static/`.

## Cómo extender la API

1. Nueva vista en `stock/api.py` (función + `@require_GET`).
2. Ruta en `stock/urls.py` bajo `api/`.
3. Si expone un campo nuevo de `Product`, añádelo a la whitelist de
   `_product_payload` — y verifica que no sea información interna
   (`average_cost`, `stock`).
4. Documentar el endpoint en este archivo y seguir el checklist de
   [`mantenimiento.md`](mantenimiento.md#cambio-en-la-api-pública).
