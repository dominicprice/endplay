from contextlib import ContextDecorator

__version__: str
__version_info__: tuple
__author__: str
__buildtime__: str

use_unicode: bool

class suppress_unicode(ContextDecorator):
    def __enter__(self): ...
    def __exit__(self, *exc): ...
