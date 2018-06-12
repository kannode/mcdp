# -*- coding: utf-8 -*-
from decorator import decorator


def memoize_simple_old(obj):
    cache = obj.cache = {}

    def memoizer(f, *args):
        key = args
        if key not in cache:
            cache[key] = f(*args)
        assert key in cache

        try:
            cached = cache[key]
            return cached
        except ImportError:  # pragma: no cover  # impossible to test
            del cache[key]
            cache[key] = f(*args)
            return cache[key]

            # print('memoize: %s %d storage' % (obj, len(cache)))

    return decorator(memoizer, obj)


def memoize_simple(obj):
    cache = obj.cache = {}

    def memoized(*args, **kwargs):
        fields = tuple(kwargs)
        values = tuple([kwargs[_] for _ in fields])
        key = (args, fields, values)
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        assert key in cache
        try:
            cached = cache[key]
            return cached
        except ImportError:  # pragma: no cover  # impossible to test
            del cache[key]
            cache[key] = obj(*args)
            return cache[key]

            # print('memoize: %s %d storage' % (obj, len(cache)))

    memoized.__name__ = obj.__name__
    return memoized
