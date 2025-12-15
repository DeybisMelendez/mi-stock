from django import template
register = template.Library()


@register.filter
def getattribute(obj, attr):
    """
    Permite acceder a atributos anidados:
    category__name → obj.category.name
    """
    try:
        for part in attr.split("__"):
            obj = getattr(obj, part)
        return obj
    except Exception:
        return ""
