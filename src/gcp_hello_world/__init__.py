"""My Project package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("my-project")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"
