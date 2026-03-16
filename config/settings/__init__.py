from decouple import config

ENVIRONMENT = config('ENVIRONMENT', default='local')

if ENVIRONMENT == 'production':
    from .production import *
else:
    from .local import *
