"""Registry of all available dictionary providers.

To add a new provider:
1. Implement a subclass of `Provider` in its own module under this package.
2. Import it here and add it to `__all__`.
"""

from .cambridge import CambridgeDictionaryProvider

__all__ = [
    "CambridgeDictionaryProvider",
]
