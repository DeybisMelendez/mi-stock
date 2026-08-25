# Autenticación

Mi Stock usa el sistema de autenticación estándar de Django
(`django.contrib.auth`). No hay OAuth, JWT, registro público ni
recuperación de contraseña personalizada.

## Configuración

En `mistock/settings.py`:

```python
INSTALLED_APPS = [
    ...
    "django.contrib.auth",
    ...
]

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
```

En `mistock/urls.py`:

```python
path("accounts/", include("django.contrib.auth.urls")),
```

Esto monta las rutas estándar de Django:

- `/accounts/login/` → `django.contrib.auth.views.LoginView`
- `/accounts/logout/` → `django.contrib.auth.views.LogoutView`
- `/accounts/password_change/` y siguientes
- `/accounts/password_reset/` y siguientes

> En este proyecto no hay templates custom para password reset/change.
> Si se accede a esas URLs sin un template propio, Django usará los
> templates por defecto del admin. No hay flujo implementado más allá
> de login/logout.

## Login

- **URL**: `/accounts/login/`
- **Template**: `templates/registration/login.html`
- **Form**: `django.contrib.auth.forms.AuthenticationForm` (el estándar)
- Tras login correcto: redirige a `LOGIN_REDIRECT_URL = "/"`.

El navbar muestra el botón "Iniciar sesión" solo si
`user.is_authenticated` es falso.

## `@login_required` en todas las vistas

Todas las vistas de `stock/views.py` llevan el decorador
`@login_required`. Si un usuario no autenticado intenta acceder, Django
lo redirige a `/accounts/login/?next=<url_original>`.

```python
@login_required
def home(request):
    ...
```

Si añades una vista nueva, **no olvides** el decorador. La excepción
es cualquier vista que intencionalmente sea pública. En este proyecto
la única es la **API pública de productos** (`stock/api.py`): vistas
`api_product_list` y `api_product_detail`, de solo lectura y sin
datos sensibles (no exponen `average_cost` ni `stock`). Ver
[`api.md`](api.md).

## Logout

- **URL**: `/accounts/logout/`
- En `templates/user_profile.html` hay un `<form method="post"
  action="{% url 'logout' %}">` con `{% csrf_token %}` y un botón
  "Cerrar sesión".
- Tras logout, redirige a `LOGOUT_REDIRECT_URL = "/"` (la raíz, que
  mostrará el navbar con "Iniciar sesión").

> **Nota**: en versiones recientes de Django, `LogoutView` requiere
> POST para evitar CSRF. El template ya hace POST correctamente.

## Crear usuarios

No hay registro público. Los usuarios se crean desde el admin de Django
(`/admin/`) o por línea de comandos:

```bash
python manage.py createsuperuser
```

> **Importante**: hasta que exista al menos un usuario, la app es
  inaccesible (todas las vistas redirigen a login, y sin usuario no
  puedes loguearte). Crea el superusuario antes de probar la app.

## Mensajes al usuario

Tras login/logout, Django puede mostrar mensajes
(`django.contrib.messages`). El template
`templates/includes/messages.html` los renderiza con un `<article>`
descartable via AlpineJS:

```html
<article x-data="{show : true}" x-show="show">
    {{ message }}
    <button class="delete" ... @click="show=false">
        <i class="material-icons">delete</i>
    </button>
</article>
```

Esto vive en `templates/layout.html` justo antes del bloque de
contenido (`{% block content %}`).

## Restricciones de contraseña

`settings.py` activa los cuatro validadores estándar:

- `UserAttributeSimilarityValidator`
- `MinimumLengthValidator`
- `CommonPasswordValidator`
- `NumericPasswordValidator`

Para modificarlos (p. ej. cambiar la longitud mínima), edita
`AUTH_PASSWORD_VALIDATORS` en `settings.py`.

## Cómo añadir una vista pública

Si necesitas exponer algo sin login (poco probable):

```python
from django.contrib.auth.decorators import login_required

def vista_publica(request):
    ...
```

No añadas `@login_required`. Pero ten en cuenta que romper esa
convención puede exponer datos sensibles — verifica antes.

## Cómo añadir login social (OAuth, etc.)

No soportado actualmente. Para añadirlo:

1. Instalar `django-allauth` (o lo que prefieras).
2. Configurar providers en `settings.py`.
3. Actualizar `INSTALLED_APPS` y `urls.py`.
4. Documentar el cambio en este archivo y en
   [`docs/mantenimiento.md`](mantenimiento.md).