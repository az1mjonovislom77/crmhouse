from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    s.strip()
    for s in config('ALLOWED_HOSTS', default='').split(',')
    if s.strip()
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': '5432',
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING["handlers"]["console"]["formatter"] = "json"
LOGGING["handlers"]["file"] = {
    "class": "logging.handlers.TimedRotatingFileHandler",
    "filename": LOGS_DIR / "app.log",
    "when": "midnight",
    "backupCount": 30,
    "formatter": "json",
    "encoding": "utf-8",
}
LOGGING["root"]["handlers"] = ["console", "file"]
LOGGING["loggers"]["django"]["handlers"] = ["console", "file"]
LOGGING["loggers"]["api.requests"]["handlers"] = ["console", "file"]
LOGGING["loggers"]["common"]["handlers"] = ["console", "file"]
