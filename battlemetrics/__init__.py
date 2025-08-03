import logging

from .client import *
from .errors import *

__version__ = "2.0a"

logging.getLogger(__name__).addHandler(logging.NullHandler())
