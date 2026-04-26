import importlib.metadata

from .convlogpy import ConflictKeyError, ConvLogPy, Formatter

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "1.0.0"  # Fallback

__all__ = ["ConvLogPy", "ConflictKeyError", "Formatter"]
