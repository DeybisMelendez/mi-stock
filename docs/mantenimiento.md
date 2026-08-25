# Mantenimiento de la documentación

Esta carpeta es la fuente de verdad sobre el proyecto. Cualquier cambio
de funcionalidad **debe** ir acompañado de la actualización de los
documentos correspondientes. Este archivo es el checklist.

## Regla general

> Si tocas código, toca docs. Si tu cambio no está reflejado en
> `docs/`, el cambio no está terminado.

`opencode.json` ya carga `docs/*.md` y `README.md` como instrucciones,
así que los cambios en la documentación llegan al contexto de futuros
agentes automáticamente.

## Checklist por tipo de cambio

### Nuevo modelo en `stock/models.py`

1. [`docs/modelos.md`](modelos.md) — sub-apartado nuevo: campos, FKs
   (con `on_delete` y `related_name`), `Meta.ordering`, métodos.
2. [`docs/migraciones.md`](migraciones.md) — entrada en la tabla
   cronológica.
3. [`docs/importar-exportar.md`](importar-exportar.md) — si quieres
   que entre al backup, sigue el procedimiento "Añadir un modelo al
   export/import".
4. [`docs/README.md`](../README.md) (raíz) si la app crece con una
   sección nueva.
5. Si el modelo es tipo CRUD simple, sigue también "Nuevo modelo CRUD
   simple" abajo.

### Nuevo campo en un modelo existente

1. [`docs/modelos.md`](modelos.md) — actualizar la tabla del modelo.
2. [`docs/migraciones.md`](migraciones.md) — entrada en la tabla
   cronológica.
3. Si el campo sale en una lista:
   - [`docs/vistas-y-urls.md`](vistas-y-urls.md) — actualizar
     `fields`/`columns`/`case` correspondiente en
     `generic_list_view`.
   - [`docs/frontend.md`](frontend.md) — mencionar si cambia el
     comportamiento de Grid.js.
4. Si el campo aparece en una factura:
   - [`docs/formularios.md`](formularios.md) — `Meta.fields` del form.
   - [`docs/frontend.md`](frontend.md) — columnas de
     `invoice_form.html` y `invoice_detail.html`.
5. Si es un campo de stock/costo:
   - [`docs/logica-stock-costo.md`](logica-stock-costo.md) — actualizar
     la lógica si la mutación cambia.

### Nuevo modelo CRUD simple

1. Modelo en `stock/models.py` + migración.
2. `ModelForm` en `stock/forms.py`.
3. Registro en `stock/admin.py`.
4. **Actualizar `views.py`**:
   - Añadir a `MODEL_NAME_MAP` si la clave difiere del nombre
     capitalizado.
   - Añadir `case` en `generic_list_view` con `fields`, `columns`,
     `title`, `queryset`, `page_obj`.
   - Añadir `case` en `generic_form_view` con `form_class` y
     `title`.
   - Añadir el `model_str` a los `valid_models` de ambas vistas.
5. **Actualizar `urls.py`**: añadir el `model_str` a los dos
   `re_path` (list y form).
6. Documentar en [`docs/modelos.md`](modelos.md),
   [`docs/vistas-y-urls.md`](vistas-y-urls.md) y
   [`docs/formularios.md`](formularios.md).
7. Añadir entrada en este checklist si creas un nuevo patrón
   recurrente.

### Cambio en `Purchase.save()` / `Purchase.delete()` / `Sale.save()` / `Sale.delete()`

> **Cambio crítico**. Actualizar **obligatoriamente** y con detalle:

1. [`docs/logica-stock-costo.md`](logica-stock-costo.md) — reescribir
   la sección afectada. Mantener el flujo "revertir y aplicar".
2. [`docs/modelos.md`](modelos.md) — actualizar la descripción de
   `Purchase` o `Sale` si cambia la semántica.
3. Si cambias los campos copiados (precio, costo), actualizar
   [`docs/formularios.md`](formularios.md).
4. **Probar manualmente** siguiendo el flujo de
   [`docs/logica-stock-costo.md#cómo-probar-cambios-en-esta-lógica`](logica-stock-costo.md#cómo-probar-cambios-en-esta-lógica).

### Nueva vista o ruta

1. [`docs/vistas-y-urls.md`](vistas-y-urls.md) — añadir entrada al
   mapa URL → vista y descripción del comportamiento.
2. [`docs/urls.md`](vistas-y-urls.md#mapa-url--vista) — fila nueva en
   la tabla.
3. Si añade un template nuevo, documentar en
   [`docs/frontend.md`](frontend.md).
4. Si requiere un form nuevo, documentar en
   [`docs/formularios.md`](formularios.md).

### Cambio en un form o formset

1. [`docs/formularios.md`](formularios.md) — actualizar la tabla de
   forms simples o la sección correspondiente.
2. Si cambia la validación (campo nuevo, widget nuevo),
   [`docs/frontend.md`](frontend.md) si el template muestra algo
   distinto.
3. Si el formset cambia las líneas de factura, **también**
   [`docs/frontend.md`](frontend.md) sección `invoice_form.html`.

### Nueva migración con reshape de datos

1. [`docs/migraciones.md`](migraciones.md) — entrada en la tabla
   cronológica.
2. **Bloque de advertencia** si la migración no es reversible sobre
   datos reales, siguiendo el estilo del bloque "⚠️ 0004–0006".
3. Actualizar [`docs/importar-exportar.md`](importar-exportar.md) si
   cambia el formato JSON.
4. Actualizar `version` en `metadata` del backup si rompe
   compatibilidad.
5. Actualizar [`docs/modelos.md`](modelos.md) si cambia el esquema.

### Cambio en import/export

1. [`docs/importar-exportar.md`](importar-exportar.md) — actualizar
   formato, orden de modelos, advertencias.
2. Si cambia el modelo añadido, [`docs/modelos.md`](modelos.md).
3. Si cambia la UI, [`docs/frontend.md`](frontend.md) sección
   `import_form.html`.

### Cambio en autenticación

1. [`docs/autenticacion.md`](autenticacion.md) — actualizar la
   sección afectada.
2. Si cambia el flujo de login/logout, [`docs/frontend.md`](frontend.md)
   sección `registration/login.html` y/o `user_profile.html`.
3. Si afecta a `views.py` (nuevo `@login_required`, vista pública),
   [`docs/vistas-y-urls.md`](vistas-y-urls.md).

### Cambio en la API pública

1. [`docs/api.md`](api.md) — actualizar endpoints, formato de
   respuesta, campos o CORS.
2. [`API.md`](../API.md) (raíz, junto al README) — es la guía para
   **usuarios/consumidores** de la API; mantenerla sincronizada con
   cualquier cambio de endpoints, campos o formato.
3. Si se expone un campo nuevo de `Product`, añadirlo a la whitelist
   de `_product_payload` en `stock/api.py` **y** verificar que no sea
   información interna (`average_cost`, `stock`).
4. Si cambia qué vistas son públicas, [`docs/autenticacion.md`](autenticacion.md)
   y [`docs/vistas-y-urls.md`](vistas-y-urls.md).
5. Si cambia el CORS (`settings.py`), [`docs/arquitectura.md`](arquitectura.md)
   tabla de stack.

### Cambio en CSS / clase nueva

1. [`docs/estilos.md`](estilos.md) — añadir al catálogo y documentar.
2. Si la clase se usa en un template, [`docs/frontend.md`](frontend.md)
   solo si cambia el patrón de uso.

### Cambio en template / JS inline

1. [`docs/frontend.md`](frontend.md) — actualizar la sección del
   template afectado.
2. Si añades un CDN nuevo (Chart.js en otra página, por ejemplo),
   [`docs/arquitectura.md`](arquitectura.md) tabla de stack.

### Cambio en arquitectura (settings, INSTALLED_APPS, etc.)

1. [`docs/arquitectura.md`](arquitectura.md) — actualizar la sección
   correspondiente.
2. Si afecta a URLs/forms, los docs respectivos.

## Verificación rápida

Tras hacer cambios, antes de pedir revisión:

- [ ] ¿Busqué en `docs/` si algún archivo menciona el componente que
      cambié?
- [ ] ¿Actualicé los archivos relevantes?
- [ ] ¿Los enlaces internos (`docs/foo.md`) siguen apuntando a archivos
      que existen?
- [ ] Si cambié comportamiento visible para el usuario, ¿actualicé
      `docs/frontend.md`?
- [ ] Si toqué `Purchase`/`Sale.save()|delete()`, ¿revisé el flujo de
      prueba manual en
      [`docs/logica-stock-costo.md`](logica-stock-costo.md#cómo-probar-cambios-en-esta-lógica)?
- [ ] Si añadí un modelo, ¿está en
      `models_to_export` / `models_order` en `views.py`?

## Convenciones al escribir docs

- **Idioma**: español. Mismo idioma que los comentarios del código.
- **Tono**: claro, directo, sin relleno.
- **Estructura**: usa encabezados `##` y `###`. Tablas Markdown cuando
  ayude a escanear.
- **Enlaces**: rutas relativas entre archivos (`../foo.md` o
  `archivo.md`).
- **Código**: bloques con `python`, `django`, `bash` según
  corresponda. Para Django templating usa `django`.
- **No añadas emojis** salvo que ya existieran en el archivo que
  editas.
- **Mantén las secciones en el mismo orden** dentro de cada archivo.
  Si añades una sección, ponla donde encaje por jerarquía, no al final
  por defecto.
- **No dupliques información** que ya esté en otro doc. En su lugar,
  enlaza.

## Cuándo pedir ayuda

Si tu cambio no encaja en ninguno de los casos anteriores:

1. Lee el doc más cercano a tu cambio.
2. Si la estructura actual no cubre tu caso, **añade una sección** al
   doc que corresponda, no crees uno nuevo.
3. Si crees que necesitas un doc completamente nuevo, pregunta antes
   de crearlo (es preferible mantener pocos archivos bien organizados
   que muchos pequeños redundantes).