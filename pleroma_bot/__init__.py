import os
import logging

__version__ = "0.5.0"

log_path = os.path.join(os.getcwd(), "error.log")

logger = logging.getLogger(__name__)

c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(log_path)
c_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.ERROR)

c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
f_format = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

logger.addHandler(c_handler)
logger.addHandler(f_handler)

from .cli import *
