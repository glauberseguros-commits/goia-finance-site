from functools import lru_cache

@lru_cache(maxsize=128)
def cached(key, factory):
    return factory()
