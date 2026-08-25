# Documentación de Mi Stock

Bienvenido a la documentación técnica del proyecto. Esta carpeta es la fuente
de verdad sobre cómo funciona el código; cualquier cambio de funcionalidad
debe reflejarse aquí (ver `docs/mantenimiento.md`).

> **Nota para agentes**: `opencode.json` ya carga `docs/*.md` y `README.md`
> como instrucciones, así que el contenido de esta carpeta forma parte del
> contexto que recibes al trabajar en el proyecto. Léelo antes de proponer
> cambios.

## Índice

| Documento | Qué cubre |
|---|---|
| [`arquitectura.md`](arquitectura.md) | Vista global del proyecto: apps Django, stack, capas |
| [`modelos.md`](modelos.md) | Cada modelo: campos, relaciones, `Meta`, métodos |
| [`logica-stock-costo.md`](logica-stock-costo.md) | Lógica de `save()`/`delete()` que muta `Product.stock` y `average_cost` |
| [`vistas-y-urls.md`](vistas-y-urls.md) | Catálogo de vistas, mapeo URL → vista, sistema genérico CRUD |
| [`formularios.md`](formularios.md) | Forms y formsets (incluye `inlineformset_factory`) |
| [`migraciones.md`](migraciones.md) | Historial de migraciones y advertencias de rollback |
| [`importar-exportar.md`](importar-exportar.md) | Formato JSON de respaldo y restauración |
| [`autenticacion.md`](autenticacion.md) | Login, `@login_required`, redirecciones |
| [`api.md`](api.md) | API pública de productos (solo lectura): endpoints, formato, CORS |
| [`frontend.md`](frontend.md) | Templates, Pico+AlpineJS+Chart.js+Grid.js, convenciones |
| [`estilos.md`](estilos.md) | Guía de CSS (BEM-light, tokens propios, anti-patrones) |
| [`mantenimiento.md`](mantenimiento.md) | Checklist: qué doc actualizar ante cada tipo de cambio |

## Cómo está organizado el repositorio

```
.
├── manage.py
├── mistock/              # Paquete de proyecto (settings, urls, wsgi, asgi)
├── stock/                # App única con toda la lógica de negocio
│   ├── models.py         # Modelos del dominio
│   ├── views.py          # Vistas + formsets inline
│   ├── forms.py          # ModelForms
│   ├── api.py            # API pública de productos (solo lectura)
│   ├── urls.py           # Rutas
│   ├── admin.py          # Registro en Django admin
│   ├── templatetags/     # Filtros de plantilla (getattribute)
│   └── migrations/       # Migraciones
├── templates/            # Plantillas a nivel de proyecto (no per-app)
├── static/css/styles.css # Hoja de estilos de la app
├── docs/                 # Esta documentación
├── AGENTS.md             # Convenciones operativas para agentes
└── README.md             # Descripción general del proyecto
```

## Convenciones generales del proyecto

- **Idioma del código**: siempre en inglés (nombres de variables, funciones,
  clases, mensajes de commit).
- **Idioma de comentarios y docs**: español.
- **Estilo de programación**: simple, legible, sin complicaciones. La solución
  más sencilla suele ser la correcta.
- **Entorno virtual**: el directorio `.env/` contiene el virtualenv
  (sí, se llama `.env/` aunque sea un virtualenv, **no** un archivo de variables).
  Activar con `source .env/bin/activate`.
- **Variables de entorno**: archivo `.secret` en la raíz, cargado con
  `load_dotenv(dotenv_path=".secret")` desde `mistock/settings.py`.
  Claves: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`.
- **Base de datos**: SQLite en `db.sqlite3`. Backups manuales `db.bak*.sqlite3`
  en la raíz, no gestionados por Django.
- **Pruebas**: `stock/tests.py` está vacío, no hay suite de tests efectiva.

## Comandos útiles

```bash
# Activar entorno
source .env/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Servidor de desarrollo
python manage.py runserver

# Migraciones
python manage.py makemigrations stock
python manage.py migrate

# Crear usuario (obligatorio antes de usar la app)
python manage.py createsuperuser
```

## Por dónde empezar a leer

Si nunca has visto el proyecto, lee en este orden:

1. [`arquitectura.md`](arquitectura.md) — panorama general
2. [`modelos.md`](modelos.md) — entiende el dominio
3. [`logica-stock-costo.md`](logica-stock-costo.md) — la parte más delicada
4. [`vistas-y-urls.md`](vistas-y-urls.md) — cómo se expone al usuario
5. [`frontend.md`](frontend.md) — qué ve el usuario

Si vienes a hacer un cambio, empieza por
[`mantenimiento.md`](mantenimiento.md).