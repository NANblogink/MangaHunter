import logging
import os
import sys
import time
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        level = record.levelname
        tag = {
            "DEBUG": "DBG",
            "INFO": "INF",
            "WARNING": "WRN",
            "ERROR": "ERR",
            "CRITICAL": "CRT",
        }.get(level, level)

        ts = self.DIM + datetime.fromtimestamp(record.created).strftime("%H:%M:%S") + self.RESET
        prefix = f"{ts} {color}{self.BOLD}[{tag}]{self.RESET}"
        msg = record.getMessage()

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            msg += "\n" + record.exc_text

        return f"{prefix} {msg}"


class FileFormatter(logging.Formatter):
    def format(self, record):
        ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)
        msg = record.getMessage()

        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            msg += "\n" + record.exc_text

        return f"[{ts}] [{level}] {msg}"


_log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(_log_dir, exist_ok=True)

_log_file = os.path.join(_log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")


def setup_logger(name="manga"):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG)
    console.setFormatter(ColoredFormatter())
    logger.addHandler(console)

    fh = logging.FileHandler(_log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(FileFormatter())
    logger.addHandler(fh)

    return logger


log = setup_logger()
