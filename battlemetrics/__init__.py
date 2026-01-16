import logging

from .client import *
from .errors import *

__version__ = "2.0.0"

logging.getLogger(__name__).addHandler(logging.NullHandler())
