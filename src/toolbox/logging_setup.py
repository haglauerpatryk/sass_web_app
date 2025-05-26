import logging
import traceback

from toolbox.toolbox_manager import ToolBoxManager

# ── 1) the boxed formatter logic ────────────────────────────────────────────────

class BoxFormatter:
    def format(self, record):
        # guarantee those attributes exist
        record.func_name = getattr(record, "func_name", "")
        record.func_path = getattr(record, "func_path", "")

        ts = self.formatTime(record, self.datefmt)
        header = f"[{record.levelname:<5}] @ {ts}"
        lines = [
            header,
            f"  – FUNC:    {record.func_name}",
            f"  – PATH:    {record.func_path}",
            f"  – DETAILS:",
        ]
        for ln in record.getMessage().splitlines():
            lines.append(f"       {ln}")

        sep = "#" * 80 if record.levelno >= logging.ERROR else "=" * 80
        return f"{sep}\n" + "\n".join(lines) + f"\n{sep}"


    def formatException(self, ei):
        return ""


class CleanConsoleHandler(logging.StreamHandler):
    def handleError(self, record):
        pass


class ConsoleFormatter(BoxFormatter, logging.Formatter):
    def __init__(self):
        super().__init__(fmt="%(message)s")

class VerboseFileHandler(logging.FileHandler):
    def handleError(self, record):
        # on handler failures, append their tb to the file
        err_tb = traceback.format_exc()
        with open(self.baseFilename, 'a', encoding='utf-8') as f:
            f.write("\n--- Logging error (handler failure) ---\n")
            f.write(err_tb)

class FileFormatter(BoxFormatter, logging.Formatter):
    def __init__(self):
        super().__init__(fmt="%(message)s")

    def format(self, record):
        box = BoxFormatter.format(self, record)
        if record.exc_info:
            # get the full traceback text
            tb = logging.Formatter.formatException(self, record.exc_info)
            box = f"{box}\n{tb.rstrip()}"
        return box


def configure_toolbox_logging():
    logger = logging.getLogger("toolbox")
    if logger.handlers:
        return
    logger.setLevel(logging.DEBUG)

    ch = CleanConsoleHandler()
    ch.setLevel(logging.DEBUG)
    ch.addFilter(lambda rec: (
        ToolBoxManager.DEBUG and
        (rec.levelno >= logging.ERROR or ToolBoxManager.PING)
    ))
    ch.setFormatter(ConsoleFormatter())

    fh = VerboseFileHandler("logs.txt", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(FileFormatter())

    logger.addHandler(ch)
    logger.addHandler(fh)
