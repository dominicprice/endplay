"""
The Actions classes provide a common interface for producing different
types of output from a dealer script. When a script is run, an appropriate
Actions object is constructed, and any time output is requested one of the
methods is called to format it correctly.
"""

__all__ = ["BaseActions", "TerminalActions", "LaTeXActions", "HTMLActions"]

from endplay.dealer.actions.base import BaseActions
from endplay.dealer.actions.terminal import TerminalActions
from endplay.dealer.actions.latex import LaTeXActions
from endplay.dealer.actions.html import HTMLActions
