from django import template
from django.core.cache import cache
from django.template.loader import render_to_string
import hashlib

register = template.Library()

@register.simple_tag(takes_context=True)
def cache_fragment(context, fragment_name, timeout=300, *args, **kwargs):
    """
    Cache a template fragment for better performance.
    Usage: {% cache_fragment 'customer_list' 600 customer.id %}
    """
    # Create a unique cache key based on fragment name and context
    cache_key_parts = [fragment_name]
    
    # Add context variables to make cache key unique
    for key, value in kwargs.items():
        if hasattr(value, 'id'):
            cache_key_parts.append(f"{key}_{value.id}")
        else:
            cache_key_parts.append(f"{key}_{value}")
    
    # Add user-specific context if available
    if 'request' in context and hasattr(context['request'], 'user'):
        cache_key_parts.append(f"user_{context['request'].user.id}")
    
    # Create cache key
    cache_key = hashlib.md5('_'.join(str(part) for part in cache_key_parts).encode()).hexdigest()
    
    # Try to get from cache
    cached_content = cache.get(cache_key)
    if cached_content is not None:
        return cached_content
    
    # If not in cache, render and cache the fragment
    # Note: This is a simplified version - in practice you'd need to render the actual template
    cached_content = f"<!-- Cached fragment: {fragment_name} -->"
    cache.set(cache_key, cached_content, timeout)
    
    return cached_content
