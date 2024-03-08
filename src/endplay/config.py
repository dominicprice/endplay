"""
Configuration and versioning information
"""

__all__ = [
    "__version__",
    "__version_info__",
    "__author__",
    "use_unicode",
    "suppress_unicode",
]

from contextlib import ContextDecorator

# Packages metadata, used by setuptools etc
__version__ = "0.5.8"
"""Version of the library as a string"""

__version_info__ = (0, 5, 8)
"""Version of the library as a tuple of integers"""

__author__ = "Dominic Price"
"""Author of the library"""

use_unicode = True
"""If set to False, the library will only print characters in the ASCII range"""


class suppress_unicode(ContextDecorator):
    """
    Context manager to temporarily ensure that unicode output is turned off,
    for example when writing to a file which expects suit symbols to be
    SDHC.

    Example usage::

            print(Denom.hearts.abbr) # prints ♥ (assuming config.use_unicode=True)
            with suppress_unicode():
                    print(Denom.hearts.abbr) # prints H
            print(Denom.hearts.abbr) # prints ♥
    """

    def __enter__(self):
        global use_unicode
        self.use_unicode = use_unicode
        use_unicode = False
        return self

    def __exit__(self, *exc):
        global use_unicode
        use_unicode = self.use_unicode
        return False
