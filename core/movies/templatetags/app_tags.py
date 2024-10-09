from django import template

from movies.models import Movie

register = template.Library()

@register.filter(name='range')
def filter_range(start, end):
    return range(start, end)

@register.filter(name='rev_range')
def filter_rev_range(start, end):
    return range(start, end, -1)