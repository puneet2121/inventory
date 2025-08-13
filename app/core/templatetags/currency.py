from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()


def _to_decimal(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _format_indian_number(n: Decimal, places: int = 2) -> str:
    negative = n < 0
    n = abs(n)
    q = Decimal(10) ** -places
    n = n.quantize(q)
    s = f"{n}"
    if "." in s:
        int_part, frac_part = s.split(".")
    else:
        int_part, frac_part = s, ""
    # Indian grouping: last 3 digits, then groups of 2
    if len(int_part) > 3:
        last3 = int_part[-3:]
        rest = int_part[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        int_part_formatted = ",".join(groups + [last3])
    else:
        int_part_formatted = int_part
    if places > 0:
        frac_part = (frac_part + "0" * places)[:places]
        number = f"{int_part_formatted}.{frac_part}"
    else:
        number = int_part_formatted
    return f"-{number}" if negative else number


@register.filter(name="rupee")
def rupee(value, places: int = 2):
    """
    Format a numeric value with the Indian Rupee symbol and Indian numbering format.
    Usage: {{ amount|rupee }} or {{ amount|rupee:0 }}
    """
    n = _to_decimal(value)
    if n is None:
        return "₹0.00" if places != 0 else "₹0"
    return f"₹{_format_indian_number(n, int(places))}"
