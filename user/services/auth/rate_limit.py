from django.core.cache import cache

LOGIN_LIMIT = 7
LOGIN_TTL = 60


def check_login_rate_limit(ip, identifier):
    key = f"login:{ip}:{identifier}"
    attempts = cache.get(key, 0)

    if attempts >= LOGIN_LIMIT:
        return False

    if attempts == 0:
        cache.set(key, 1, LOGIN_TTL)
    else:
        cache.incr(key)

    return True


def reset_login_rate_limit(ip, identifier):
    key = f"login:{ip}:{identifier}"
    cache.delete(key)
