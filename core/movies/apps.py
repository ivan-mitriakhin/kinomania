from django.apps import AppConfig

import redis

from core import settings

class MoviesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'movies'

    redis_client = redis.from_url(settings.CACHES.get('default').get('LOCATION'))

    def ready(self):
        import movies.signals # noqa
