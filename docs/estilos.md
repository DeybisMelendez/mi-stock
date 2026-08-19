# Guía de estilos de Mi Stock

Esta guía explica cómo está organizada la hoja de estilos de la aplicación y cómo
añadir o modificar reglas sin romper la compatibilidad con Pico CSS ni con los
temas claro/oscuro.

## 1. Archivos del sistema de estilos

| Archivo | Propósito |
|---|---|
| `static/css/styles.css` | Hoja de estilos de la app. Complementa Pico CSS. |
| `static/css/styles.css` se enlaza en `templates/layout.html` mediante `{% load static %}` y `{% static 'css/styles.css' %}`. |
| `mistock/settings.py` | Define `STATICFILES_DIRS = [BASE_DIR / "static"]` para que Django sirva el archivo en `runserver`. |

No debe haber `<style>` dentro de las plantillas y no debe haber atributos
`style=""` en el HTML. Todo el estilo vive en `styles.css`.

## 2. Compatibilidad con Pico CSS

Pico CSS tiene sus propias variables (`--pico-color-*`, `--primary`, `--secondary`,
`--success`, `--error`, `--muted-color`, `--muted-border-color`, etc.) y las
redefine cuando el usuario cambia entre tema claro y oscuro.

`styles.css` **no redefine** esas variables. Solo las consume. Por eso, cuando
se cambia el tema en Pico, todos los colores de la app cambian automáticamente.

Las únicas variables de color que la app añade son los **tokens propios** en
`:root` al inicio del archivo, y todas derivan de variables de Pico. Ejemplo:

```css
:root {
    --ms-border: 1px solid var(--muted-border-color);
}
```

Si en el futuro quieres soportar temas con identidad de marca que difieran del
default de Pico, basta con cambiar los valores de `--pico-*` (o sobreescribirlos
en un bloque propio); los componentes de la app los heredarán.

## 3. Convenciones de nombres

La nomenclatura usada es **BEM-light**:

- **Bloque**: `kpi-card`, `alert-list`, `tabs-bar`, `table-stripped`.
- **Elemento**: `kpi-card__title`, `kpi-card__value`, `tabs-bar__head`.
- **Modificador**: `kpi-card--primary`, `kpi-card--success`, `kpi-card--danger`,
  `kpi-card--secondary`, `icon--gap-sm`, `icon--gap-md`, `grid--cards`,
  `grid--charts`, `grid--panels`.

Reglas:

- Toda regla nueva usa **clases**, nunca IDs (excepto `#gridjs-table`, que es
  parte contractual de Grid.js) ni selectores por tag.
- Los modificadores nunca se usan solos: siempre junto al bloque base.
  Ejemplo: `<article class="kpi-card kpi-card--success">`.

## 4. Estructura del archivo `styles.css`

El archivo está organizado en secciones marcadas con comentarios-encabezado.
Al añadir reglas, ubícalas en la sección correspondiente para que el archivo
se mantenga ordenado:

1. **Tokens** (`/* === Tokens propios === */`): variables `--ms-*`.
2. **Utilidades** (`/* === Utilidades === */`): clases de propósito único.
3. **Iconos** (`/* === Iconos === */`): reset para Material Icons.
4. **Layouts** (`/* === Layouts === */`): variantes de grid y separadores.
5. **Componentes** (`/* === Componentes === */`): bloques reusables.
6. **Grid.js** (`/* === Grid.js === */`): estilos para la integración con Pico.

## 5. Catálogo de clases

### 5.1 Utilidades

| Clase | Uso | Ejemplo |
|---|---|---|
| `.muted` | Texto secundario | `<small class="muted">Detalle</small>` |
| `.text-success` | Texto verde (positivos) | `<span class="text-success">↗ 12%</span>` |
| `.text-error` | Texto rojo (negativos) | `<span class="text-error">↘ 5%</span>` |
| `.text-warning` | Texto ámbar (avisos) | `<span class="text-warning">Atención</span>` |
| `.text-end` | Alinear a la derecha | `<th class="text-end">Total</th>` |
| `.text-start` | Alinear a la izquierda | `<td class="text-start">Nombre</td>` |
| `.text-small` | Tamaño 0.9rem | `<a class="text-small">Ver todos</a>` |
| `.hidden` | Ocultar completamente | `<div class="hidden">plantilla</div>` |
| `.stack-sm` | `margin-bottom: 1rem` | `<div class="stack-sm">…</div>` |
| `.stack-md` | `margin-bottom: 2rem` | `<header class="stack-md">…</header>` |
| `.stack-lg` | `margin-bottom: 3rem` | `<header class="stack-lg">…</header>` |
| `.flex-between` | Flex space-between + center | `<div class="flex-between">…</div>` |

### 5.2 Iconos

Material Icons se carga desde el CDN al inicio de `layout.html`. Para usarlo
correctamente:

```html
<a href="...">
    <span class="icon icon--gap-md">inventory_2</span>Productos
</a>
```

- `.icon` aplica tamaño y alineación base.
- `.icon--gap-sm` agrega 4px a la derecha (usar en `<summary>` del dropdown).
- `.icon--gap-md` agrega 6px a la derecha (usar en items del menú y en botones
  con icono).

Para enlaces formados únicamente por un icono (caso típico de las acciones de
Grid.js), no se necesita una clase extra: el contenedor de Grid.js ya aporta
los estilos. Si añades un enlace directo con icono+etiqueta, considera
`.icon-link` para quitar el subrayado bajo el icono.

### 5.3 Layouts

| Clase | Uso |
|---|---|
| `.section-stack` | Separador grande entre secciones del dashboard (`margin-bottom: 3rem`). |
| `.grid--cards` | Grid responsivo para tarjetas KPI (min 250px). |
| `.grid--charts` | Grid para gráficos (min 300px, gap 2rem). |
| `.grid--panels` | Grid para paneles laterales (min 280px, gap 2rem). |

Todas se aplican **junto** a `.grid` (que viene de Pico):

```html
<div class="grid grid--cards">…</div>
```

### 5.4 Componentes

#### Tarjeta KPI

```html
<article class="kpi-card kpi-card--primary">
    <header>
        <h3 class="kpi-card__title">Ventas del Mes</h3>
    </header>
    <p class="kpi-card__value">C$ 12,500.00</p>
    <footer class="kpi-card__footer">
        <span class="text-success">↗ 12.5%</span> vs mes anterior
    </footer>
</article>
```

Modificadores disponibles: `kpi-card--primary`, `kpi-card--secondary`,
`kpi-card--success`, `kpi-card--danger`. Cada uno cambia el color del borde
izquierdo.

#### Tablas responsivas

```html
<div class="table-wrap">
    <table>
        <!-- tabla estándar de Pico -->
    </table>
</div>
```

Si necesitas una tabla **sin bordes** de Pico (caso típico de tablas pequeñas
como "productos más vendidos" del dashboard), usa `.table-stripped`:

```html
<table class="table-stripped">
    <thead>
        <tr>
            <th class="text-start">Producto</th>
            <th class="text-end">Cantidad</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Coca-Cola</td>
            <td class="text-end">50</td>
        </tr>
    </tbody>
</table>
```

`.table-stripped` aplica bordes finos, padding uniforme y ancho 100%.
Las celdas numéricas deben llevar `.text-end` para alinearse a la derecha.

#### Tabs (AlpineJS)

```html
<div role="tablist" class="tabs-bar">
    <button role="tab" :class="tab === 'mes' ? 'contrast' : 'outline'"
            @click="tab = 'mes'">Mes</button>
    <!-- … -->
</div>

<div class="flex-between tabs-bar__head">
    <small class="muted">Agosto 2026</small>
    <a href="..." class="text-small">Ver todos</a>
</div>
```

#### Listas de alertas

```html
<ul class="alert-list">
    <li><a href="...">Coca-Cola</a></li>
    <li><a href="...">Pepsi</a></li>
</ul>
```

#### Miniaturas de productos

```html
<!-- Tabla de fotos en product_detail.html -->
<img class="thumb-md" src="..." alt="Foto">

<!-- Lista de fotos en product_form.html -->
<img class="thumb-sm" src="..." alt="">
```

### 5.5 Grid.js

Grid.js inserta su propio DOM en `#gridjs-table`. Las reglas en `styles.css`
aseguran que:

- el wrapper haga scroll horizontal en celulares,
- el header no muestre el icono de orden interno de Grid.js (se reemplaza por
  el icono de Material Icons definido en `list.html`),
- las celdas no tengan un `min-width` artificial,
- el contenedor ocupe todo el ancho.

No deberías necesitar añadir reglas nuevas para Grid.js. Si lo haces, agrégalas
en la sección `/* === Grid.js === */` al final del archivo.

## 6. Cómo añadir un componente nuevo

Sigue este checklist:

1. **Define el bloque** en `styles.css` dentro de la sección `Componentes`,
   usando nomenclatura BEM-light. Ejemplo:

   ```css
   .mi-card {
       padding: var(--ms-space-4);
       border-radius: var(--ms-radius);
   }

   .mi-card--warning {
       border-left: 4px solid var(--pico-color-amber-500, #f59e0b);
   }
   ```

2. **Si el valor se repite**, promuévelo a token en la sección `Tokens`
   al inicio del archivo:

   ```css
   :root {
       --ms-warning-color: var(--pico-color-amber-500, #f59e0b);
   }

   .mi-card--warning {
       border-left: 4px solid var(--ms-warning-color);
   }
   ```

3. **Documenta la clase** en la sección 5 de este archivo (catálogo): propósito,
   ejemplo de HTML, modificadores disponibles.

4. **Úsala en la plantilla** con `class="…"`. Nunca con `style=""`.

## 7. Anti-patrones (NO hacer)

- ❌ `style="color: red"` en cualquier plantilla.
- ❌ `<style>…</style>` dentro de una plantilla.
- ❌ `!important` salvo `.hidden` (donde se necesita asegurar que el elemento
  quede oculto aunque otras reglas intenten mostrarlo).
- ❌ Redefinir `--pico-*` u otras variables de Pico. Si necesitas un color
  nuevo, créalo como token propio `--ms-*` o usa uno de los que ya están
  disponibles.
- ❌ Selectores por tag (`p { … }`, `table { … }`) en `styles.css`. Todas las
  reglas deben ser por clase.
- ❌ Cargar CSS desde CDN adicional sin comentar por qué (rompe la idea de una
  sola fuente de estilo).

## 8. Cambios en `settings.py`

La única línea añadida a `mistock/settings.py` es:

```python
STATICFILES_DIRS = [BASE_DIR / "static"]
```

Sin ella, `{% static 'css/styles.css' %}` devolvería un 404. No se ha tocado
`STATIC_ROOT` (`staticfiles/`), que sigue listo para `collectstatic` en producción.
