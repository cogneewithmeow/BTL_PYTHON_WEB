from django import template

register = template.Library()


@register.filter(name="dot_thousands")
def dot_thousands(value):
    """
    Format number using dot thousands separators (Vietnam style).
    Examples: 12234000 -> 12.234.000
    """
    if value is None:
        return ""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{n:,}".replace(",", ".")

