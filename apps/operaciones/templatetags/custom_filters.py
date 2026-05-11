from django import template

register = template.Library()

@register.filter
def sum_attribute(queryset, attribute):
    """Suma un atributo de una lista de objetos"""
    total = 0
    for obj in queryset:
        try:
            total += getattr(obj, attribute)
        except (TypeError, AttributeError):
            pass
    return total