from django import template

register = template.Library()


@register.filter
def get_obj_index(obj, idx):
    return obj[idx]
