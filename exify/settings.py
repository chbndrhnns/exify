from functools import lru_cache

from exify.models import ExifySettings


@lru_cache
def get_settings():
    return ExifySettings()


