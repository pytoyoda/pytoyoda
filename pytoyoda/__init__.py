"""Toyota Connected Services Client.

.. include:: ../README.md

"""

from importlib_metadata import PackageNotFoundError, version

from pytoyoda.client import MyT  # noqa : F401

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # Package is not installed, likely running from source directory
    __version__ = "0.0.0-dev"  # Or any other placeholder
