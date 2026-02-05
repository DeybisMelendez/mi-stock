from django import template
from datetime import datetime, date as date_type
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


@register.filter
def format_value(obj, attr):
    """
    Obtiene el atributo y lo formatea si es una fecha/hora.
    """
    try:
        for part in attr.split("__"):
            obj = getattr(obj, part)
        
        # Formatear si es datetime o date
        if isinstance(obj, datetime):
            return obj.strftime("%d/%m/%Y %H:%M")
        elif isinstance(obj, date_type):
            return obj.strftime("%d/%m/%Y")
        
        # Convertir a string para otros tipos
        return str(obj) if obj is not None else ""
    except Exception:
        return ""
