from django.core.cache import cache

LOGIN_LIMIT = 7
LOGIN_TTL = 60


def check_login_rate_limit(ip, identifier):
    key = f"login:{ip}:{identifier}"

    if cache.add(key, 1, LOGIN_TTL):
        return True

    try:
        attempts = cache.incr(key)
    except ValueError:
        cache.set(key, 1, LOGIN_TTL)
        return True

    return attempts <= LOGIN_LIMIT


def reset_login_rate_limit(ip, identifier):
    key = f"login:{ip}:{identifier}"
    cache.delete(key)
