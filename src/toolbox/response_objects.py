import logging
from logging import LoggerAdapter

from toolbox.toolbox_manager import ToolBoxManager

class LogManager:
    def __init__(self):
        self._logger = logging.getLogger("toolbox")


    def _make_adapter(self, extra: dict):
        # attach function‐name and path to every record
        return LoggerAdapter(self._logger, extra)


    def add_info_log(self, message: str, **context):
        """
        Emits an INFO‐level record; will appear on console
        only if DEBUG and PING are True.
        """
        if not (ToolBoxManager.DEBUG and ToolBoxManager.PING):
            return

        adapter = self._make_adapter(context)
        adapter.info(message)


    def add_error_log(self, message: str, **context):
        """
        Emits an ERROR-level record with exc_info=True;
        console will suppress it, file will keep the traceback.
        """
        if not ToolBoxManager.DEBUG:
            return

        adapter = self._make_adapter(context)
        adapter.error(message, exc_info=True)
