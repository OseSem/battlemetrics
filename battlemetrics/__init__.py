import logging
from typing import Final, Literal, NamedTuple

from .client import *
from .errors import *
from .misc import *
from .note import *
from .server import *
from .types import *

# Placeholder, modified by dynamic-versioning.
__version__: Final[str] = "0.0.0"


class VersionInfo(NamedTuple):
    """Represents the version information of the library."""

    major: int
    minor: int
    micro: int
    releaselevel: Literal["alpha", "beta", "candidate", "final"]
    serial: int
    metadata: str


# Placeholder, modified by dynamic-versioning.
version_info: VersionInfo = VersionInfo(0, 0, 0, "final", 0, "")


logging.getLogger(__name__).addHandler(logging.NullHandler())
