import os
import sys
import logging

__version__ = "0.8.0"


class StdOutFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.WARNING, logging.DEBUG, logging.INFO)


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format_r = "%(asctime)s - %(name)s - %(levelname)s - %(message)s "
    format_l = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s "
        "(%(filename)s:%(lineno)d) "
    )

    if sys.platform != "win32":
        FORMATS = {
            logging.DEBUG: grey + format_r + reset,
            logging.INFO: grey + "ℹ " + format_r + reset,
            logging.WARNING: yellow + "⚠ " + format_l + reset,
            logging.ERROR: red + "✖ " + format_l + reset,
            logging.CRITICAL: bold_red + format_l + reset,
        }
    else:
        FORMATS = {
            logging.DEBUG: format_r,
            logging.INFO: "¡ " + format_r,
            logging.WARNING: "!!" + format_l,
            logging.ERROR: "× " + format_l,
            logging.CRITICAL: "× " + format_l,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


log_path = os.path.join(os.getcwd(), "error.log")
logging.root.setLevel(logging.INFO)
logger = logging.getLogger(__name__)

c_handler = logging.StreamHandler(sys.stdout)
e_handler = logging.StreamHandler(sys.stderr)
f_handler = logging.FileHandler(log_path)
c_handler.setLevel(logging.INFO)
e_handler.setLevel(logging.ERROR)
f_handler.setLevel(logging.ERROR)

c_format = CustomFormatter()
e_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
f_format = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
c_handler.setFormatter(c_format)
e_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)
c_handler.addFilter(StdOutFilter())

logger.addHandler(c_handler)
logger.addHandler(e_handler)
logger.addHandler(f_handler)

logger.propagate = True

from .cli import *
