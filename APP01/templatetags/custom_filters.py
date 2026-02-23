from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if not isinstance(dictionary, dict):
        return None
    return dictionary.get(key)

import json

@register.filter
def get_spec(gear, key):
    """
    Parses the 'specs' JSON field of a GamingGear object and returns the value for the given key.
    Usage: {{ gear|get_spec:"Weight" }}
    """
    if not gear or not gear.specs:
        return "-"
    
    # If specs is already a dict (which it should be for JSONField), use it directly
    if isinstance(gear.specs, dict):
        return gear.specs.get(key, "-")
        
    # If specs is a string (e.g. from raw SQL or legacy data), parse it
    try:
        if isinstance(gear.specs, str):
            # Handle potential single quotes in JSON string (common in some scraped data)
            specs_str = gear.specs.replace("'", '"')
            specs_dict = json.loads(specs_str)
            return specs_dict.get(key, "-")
    except (json.JSONDecodeError, AttributeError, TypeError):
        return "-"
    
    return "-"

@register.filter
def split(value, arg):
    """
    Splits the string by the given argument.
    Usage: {{ "a,b,c"|split:"," }}
    """
    return value.split(arg)
