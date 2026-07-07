from decouple import config
from django.core.exceptions import ImproperlyConfigured

ENVIRONMENT = config('ENVIRONMENT', default='production')

if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'local':
    from .local import *
else:
    raise ImproperlyConfigured(
        f"ENVIRONMENT noto'g'ri qiymat: {ENVIRONMENT!r}. 'local' yoki 'production' bo'lishi kerak."
    )
