from django import template
from django.utils.safestring import mark_safe
import bleach
import markdown as md

register = template.Library()


# Whitelist de tags y atributos permitidos al sanitizar el HTML generado
# por el markdown. Se mantiene cerrada a propósito: si hace falta añadir
# algo (por ejemplo, atributos de estilo), se valora caso por caso.
ALLOWED_TAGS = [
    "p",
    "br",
    "hr",
    "strong",
    "em",
    "b",
    "i",
    "u",
    "ul",
    "ol",
    "li",
    "a",
    "code",
    "pre",
    "blockquote",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "img",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title"],
    "code": ["class"],
    "pre": ["class"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


@register.filter(is_safe=True)
def markdown_safe(value):
    """
    Convierte markdown a HTML y lo sanitiza.

    - Usa la extensión `nl2br` para que un salto de línea simple se
      mantenga visible (compatibilidad con descripciones previas que
      no son markdown estricto).
    - El HTML resultante pasa por `bleach.clean` con una whitelist
      cerrada para evitar XSS si la descripción proviene de fuentes
      no controladas.
    - Devuelve cadena vacía si el valor es `None` o si ocurre algún
      error de parseo.
    - Marca el resultado como `SafeString` para que Django NO lo
      escape (ya viene saneado por bleach).
    """
    if not value:
        return ""
    try:
        raw_html = md.markdown(
            str(value),
            extensions=["nl2br", "fenced_code", "tables"],
            output_format="html",
        )
        cleaned = bleach.clean(
            raw_html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,
        )
        return mark_safe(cleaned)
    except Exception:
        return ""
