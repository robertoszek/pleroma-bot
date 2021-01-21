import os
import sys
import logging

__version__ = "0.7.3"


class StdOutFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.WARNING, logging.DEBUG, logging.INFO)


log_path = os.path.join(os.getcwd(), "error.log")
logging.root.setLevel(logging.INFO)
logger = logging.getLogger(__name__)

c_handler = logging.StreamHandler(sys.stdout)
e_handler = logging.StreamHandler(sys.stderr)
f_handler = logging.FileHandler(log_path)
c_handler.setLevel(logging.INFO)
e_handler.setLevel(logging.ERROR)
f_handler.setLevel(logging.ERROR)

c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
e_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
f_format = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
c_handler.setFormatter(c_format)
e_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)
c_handler.addFilter(StdOutFilter())

logger.addHandler(c_handler)
logger.addHandler(e_handler)
logger.addHandler(f_handler)

from .cli import *
