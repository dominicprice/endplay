"""
A tkinter interface to many of the features of endplay including 
dealing hands and performing double-dummy analysis.
"""

__all__ = ["TkFrontend"]

from endplay.interact import InteractiveDeal

class TkFrontend:
    def __init__(self, deal: InteractiveDeal):
        raise NotImplementedError