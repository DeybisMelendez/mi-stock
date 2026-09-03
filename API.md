# 🌐 API de Mi Stock

Mi Stock ofrece una **API pública de solo lectura** para consultar el
catálogo de productos. No requiere autenticación ni claves: solo haz
peticiones `GET`.

Con ella puedes construir, por ejemplo:

- Una tienda web o catálogo propio.
- Una app móvil que muestre tus productos.
- Integraciones con otros sistemas (solo consulta).

> La API no permite crear, editar ni borrar nada. La gestión de
> inventario se hace desde la aplicación web.

---

## 🔗 URL base

```
https://mi-stock-alphatechni.pythonanywhere.com
```

---

## 📡 Endpoints

| Método | URL | Descripción |
|---|---|---|
| `GET` | `/api/products/` | Lista de productos activos |
| `GET` | `/api/products/{id}/` | Detalle de un producto |

Cualquier otro método (`POST`, `PUT`, `DELETE`…) devuelve
**405 Method Not Allowed**.

### ¿Qué es un "producto disponible"?

Los productos **activos**. Los productos desactivados no aparecen;
los productos agotados sí aparecen, marcados con `in_stock: false`
para que puedas distinguirlos.

---

## 📋 Lista de productos

```bash
curl https://mi-stock-alphatechni.pythonanywhere.com/api/products/
```

Respuesta:

```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "name": "Lampara Dragon Ball Gokú Pequeño",
      "description": "Lámpara LED 3D",
      "price": "850.00",
      "in_stock": true,
      "category": {"id": 1, "name": "Lampara Led 3D"},
      "tags": ["oferta", "nuevo"],
      "images": ["https://mi-stock-alphatechni.pythonanywhere.com/media/product_images/foto1.jpg"]
    },
    {
      "id": 43,
      "name": "Piramide Moyu Meilong Stickerless",
      "description": "",
      "price": "450.00",
      "in_stock": false,
      "category": {"id": 7, "name": "Cubo Mágico"},
      "tags": [],
      "images": []
    }
  ]
}
```

- `count` — cantidad de productos devueltos.
- `results` — el listado completo (no hay paginación).

---

## 🔍 Detalle de un producto

Sustituye `{id}` por el identificador del producto:

```bash
curl https://mi-stock-alphatechni.pythonanywhere.com/api/products/43/
```

Respuesta (mismo formato que los elementos de la lista):

```json
{
  "id": 43,
  "name": "Piramide Moyu Meilong Stickerless",
  "description": "",
  "price": "450.00",
  "in_stock": false,
  "category": {"id": 7, "name": "Cubo Mágico"},
  "tags": ["oferta"],
  "images": ["https://mi-stock-alphatechni.pythonanywhere.com/media/product_images/63685.jpg"]
}
```

Si el producto no existe o está inactivo, se devuelve **404** con un
cuerpo JSON:

```json
{"error": "Producto no encontrado."}
```

> Los productos agotados (stock 0) **sí** están disponibles vía el
> endpoint de detalle. Para distinguir un producto agotado de uno con
> existencias, revisa el campo `in_stock`.

---

## 🧩 Campos

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | número | Identificador del producto |
| `name` | texto | Nombre |
| `description` | texto | Descripción en **markdown plano** (vacío o `null` si no tiene). El consumidor es responsable de renderizarlo si lo desea. |
| `price` | texto | Precio de venta en córdobas, con 2 decimales (p. ej. `"450.00"`) |
| `in_stock` | boolean | `true` si el producto tiene existencias, `false` si está agotado |
| `category` | objeto | Categoría: `{id, name}` |
| `tags` | lista | Nombres de las etiquetas asignadas al producto (`[]` si no tiene) |
| `images` | lista | URLs absolutas de las fotos (`[]` si no tiene) |

Notas:

- **`price` viene como texto** para conservar la precisión decimal.
  Conviértelo a número en tu lenguaje solo si lo necesitas
  (p. ej. `parseFloat("450.00")`).
- **`in_stock` es un boolean derivado** de las existencias internas.
  No expone la cantidad exacta en inventario.
- **`images` son URLs absolutas**, listas para usar en un `<img>` o
  para descargar el archivo.
- El listado viene ordenado alfabéticamente por nombre.

Por privacidad del negocio, la API **no expone** costos internos ni
cantidades en inventario.

---

## 🌍 CORS (consumo desde el navegador)

La API envía `Access-Control-Allow-Origin: *`, así que puedes
consultarla desde JavaScript en cualquier sitio web:

```javascript
const response = await fetch("https://mi-stock-alphatechni.pythonanywhere.com/api/products/");
const data = await response.json();

data.results.forEach((product) => {
    console.log(product.name, product.price, product.in_stock ? "disponible" : "agotado");
});
```

---

## 🐍 Ejemplo en Python

```python
import requests

response = requests.get("https://mi-stock-alphatechni.pythonanywhere.com/api/products/")
data = response.json()

for product in data["results"]:
    estado = "disponible" if product["in_stock"] else "agotado"
    print(f"{product['name']} — C$ {product['price']} ({estado})")
```

---

## ❗Errores

| Código | Cuándo ocurre |
|---|---|
| `404` | El producto no existe o está inactivo |
| `405` | Se usó un método distinto de `GET` |

---

## ❓Preguntas frecuentes

**¿Necesito una API key?**
No. La API es pública y de solo lectura.

**¿Puedo crear o editar productos por la API?**
No. Toda la gestión se hace desde la aplicación web con tu usuario.

**¿Por qué un producto que veo en la app no aparece?**
Porque está inactivo. La API solo lista productos activos, aunque
estén agotados (en ese caso aparecen con `in_stock: false`).

**¿Las fotos se pueden usar directamente?**
Sí, las URLs de `images` apuntan al archivo original y se pueden
mostrar o descargar. Atribúyelas a tu propio catálogo si las publicas.
