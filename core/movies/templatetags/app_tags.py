from django import template

register = template.Library()

@register.filter(is_safe=True)
def request_poster(poster_path):    
    return f"https://image.tmdb.org/t/p/w185{poster_path}"