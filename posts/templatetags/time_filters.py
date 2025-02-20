import datetime
from django import template
from django.utils.timezone import now

register = template.Library()

@register.filter
def time_ago(value):
    """Formats datetime as 'time ago' or 'Month Day at HH:MM'."""
    if not value:
        return ""

    now_time = now()
    diff = now_time - value

    # Just now, minutes ago
    if diff.total_seconds() < 60:
        return "Just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minutes ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hours ago"

    # Check if the post is within the same year
    if now_time.year == value.year:
        return value.strftime("%B %d at %H:%M")  # Example: February 13 at 14:30
    else:
        return value.strftime("%Y %B %d at %H:%M")  # Example: 2024 February 12 at 08:15
