import logging
from importlib.metadata import PackageNotFoundError, version

from .client import *
from .errors import *

try:
    __version__ = version("battlemetrics")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

logging.getLogger(__name__).addHandler(logging.NullHandler())
