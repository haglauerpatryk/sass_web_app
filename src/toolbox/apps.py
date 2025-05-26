import os, inspect

from django.conf import settings
from django.apps import AppConfig

class ToolboxConfig(AppConfig):
    name = "toolbox"
    verbose_name = "Toolbox"

    def ready(self):
        from .logging_setup import configure_toolbox_logging
        configure_toolbox_logging()
        from .ping_manager import PingManager

        PingManager.register_provider(
            lambda self, func, args, kwargs: {
                "message": "",
                "context": {
                    "func_name": func.__name__,
                    "func_path": os.path.relpath(inspect.getfile(func), settings.BASE_DIR),
                },
            },
        )
