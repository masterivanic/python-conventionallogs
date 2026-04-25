from .convlogpy import ConvLogPy, ConflictKeyError, Formatter
import importlib.metadata

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "1.0.0"  # Fallback

__all__ = ["ConvLogPy", "ConflictKeyError", "Formatter"]
