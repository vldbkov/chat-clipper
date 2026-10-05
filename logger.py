import logging
import os
import sys
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logging")
LOG_FILE = os.path.join(LOG_DIR, "chatclipper.log")


# Output stream wrapper: replaces incompatible characters with '?' without crashing
class SafeStream:
    # Initialize wrapper
    def __init__(self, stream):
        self.stream = stream
        enc = getattr(stream, "encoding", None) or "utf-8"
        self.encoding = enc

    # Write string with safe re-encoding
    def write(self, msg):
        try:
            self.stream.write(msg)
        except UnicodeEncodeError:
            try:
                enc = self.encoding or "utf-8"
                self.stream.write(msg.encode(enc, errors="replace").decode(enc, errors="replace"))
            except Exception:
                pass
        except Exception:
            pass

    # Forward flush
    def flush(self):
        try:
            self.stream.flush()
        except Exception:
            pass

    # Forward isatty
    def isatty(self):
        try:
            return self.stream.isatty()
        except Exception:
            return False


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("ChatClipper")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    os.makedirs(LOG_DIR, exist_ok=True)
    fh = RotatingFileHandler(
        LOG_FILE, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler(SafeStream(sys.stdout))
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


log = setup_logger()