import os
import sys
import locale
import logging

__version__ = "1.0.0"


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
    else:  # pragma: win32 cover
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


logging.root.setLevel(logging.INFO)
logger = logging.getLogger(__name__)

c_handler = logging.StreamHandler(sys.stdout)
e_handler = logging.StreamHandler(sys.stderr)
c_handler.setLevel(logging.INFO)
e_handler.setLevel(logging.ERROR)

c_format = CustomFormatter()
e_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
c_handler.setFormatter(c_format)
e_handler.setFormatter(c_format)
c_handler.addFilter(StdOutFilter())

logger.addHandler(c_handler)
logger.addHandler(e_handler)

logger.propagate = True

stork = r'''
                        `^y6gB@@BBQA{,
                      :fB@@@@@@BBBBBQgU"
                    `f@@@@@@@@BBBBQgg80H~
                    H@@B@BB@BBBB#Qgg&0RNT
                   z@@&B@BBBBBBQgg80RD6HK
                  ;@@@QB@BBBB#Qgg&0RN6WqS
                  q@@@@@BBBBQgg80RN6HAqSo          _             _
                 z@@@@BBBB#Qg8&0RN6WqSUhr         | |           | |
               -H@@@@BBBBQQg80RD6HAqSKh(       ___| |_ ___  _ __| | __
              rB@@@BBBB#6Lm00DN6WqSUhfv       / __| __/ _ \| '__| |/ /
             f@@@@BBBBf= |0RD6HAqSKhfv        \__ \ || (_) | |  |   <
           =g@@@BBBBF=  "RDN6WqSUhff{         |___/\__\___/|_|  |_|\_|
          c@@@@BBgu_   ~WD9HAqSKhfkl`
        _6@@@BBNr     'qN6WqSUhhfXI'     .                           .       .
       rB@@@B0r      `S6HAqSKhfkoCr  ,-. |  ,-. ,-. ,-. ,-,-. ,-.    |-. ,-. |-
     `X@@@BQx       `I6WASShhfXFIy_  | | |  |-' |   | | | | | ,-| -- | | | | |
    _g@@@Q\`        JHAqSKhfXoCwJz_  |-' `' `-' '   `-' ' ' ' `-^    `-' `-' `'
   rB@@#x`         }WASShhfXsIyzuu,  |
 `y@@&|          .IAqSKhfXoCwJzu1lr  '
`D@&|           :KqSUhffXsIyzuu1llc,
ff=            `==:::""",,,,________

'''
if __name__ == "pleroma_bot.__init__":
    print(stork)

# fill env locale vars in case we're running in other platforms
default_lang, default_enc = locale.getdefaultlocale()

if "LANG" not in os.environ:  # pragma: win32 cover
    os.environ["LANG"] = default_lang
    os.environ["LANGUAGE"] = f"{default_lang}.{default_enc}"

from .cli import *
