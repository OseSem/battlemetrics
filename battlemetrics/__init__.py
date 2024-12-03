import logging
from typing import Final

from .client import *
from .errors import *
from .note import *
from .server import *
from .types import *

# Placeholder, modified by dynamic-versioning.
# TODO: Make this auto update.
__version__: Final[str] = "0.0.0"


logging.getLogger(__name__).addHandler(logging.NullHandler())
