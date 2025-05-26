from django.conf import settings

from toolbox.toolbox_manager import ToolBoxManager

class PingManager:
    ping_providers = []
    base_dir = settings.BASE_DIR


    @classmethod
    def register_provider(cls, fn):
        """Call this at startup to add more providers."""
        if fn not in cls.ping_providers:
            cls.ping_providers.append(fn)


    def _collect_pings(self, func, args, kwargs):
        if not ToolBoxManager.PING:
            return []
        return [
            provider(self, func, args, kwargs)
            for provider in self.__class__.ping_providers
        ]


    def get_ping_decorator(self):
        def decorator(func):
            from functools import wraps
            @wraps(func)
            def wrapped(*args, **kwargs):
                if ToolBoxManager.PING:
                    # each provider now returns a {message, context} dict
                    payloads = [
                        provider(self, func, args, kwargs)
                        for provider in self.__class__.ping_providers
                    ]
                    # combine into one INFO call
                    msgs = [p["message"] for p in payloads]
                    merged_ctx = {}
                    for p in payloads:
                        merged_ctx.update(p.get("context", {}))

                    combined = "\n".join(msgs)
                    self.log_manager.add_info_log(combined, **merged_ctx)

                return func(*args, **kwargs)
            return wrapped
        return decorator

