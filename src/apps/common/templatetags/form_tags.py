from __future__ import annotations

from django import template
from django.forms import BoundField

register = template.Library()


@register.filter
def add_class(field: BoundField, css_class: str) -> str:
    """Render a BoundField widget with extra CSS class(es) merged in."""
    existing = field.field.widget.attrs.get("class", "")
    merged = f"{existing} {css_class}".strip() if existing else css_class
    return field.as_widget(attrs={"class": merged})
