from django import template
from payment.models import OrderItem

register = template.Library()

@register.filter
def has_purchased(user, product):
    """
    Check if a user has purchased a specific product
    Usage: {% if user|has_purchased:product %}
    """
    return OrderItem.objects.filter(
        product=product,
        user=user,
        order__isnull=False  # Only count completed orders
    ).exists()
