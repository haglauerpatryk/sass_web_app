from django.conf import settings
from decouple import config

class ToolBoxManager:
    DEBUG = settings.DEBUG
    PING = config("PING", default=False, cast=bool)
