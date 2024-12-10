import logging
from typing import Final

from .client import *
from .errors import *
from .note import *
from .server import *
from .types import *

__version__: Final[str] = "2.0"


logging.getLogger(__name__).addHandler(logging.NullHandler())
