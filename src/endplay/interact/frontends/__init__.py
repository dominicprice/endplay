"""
Frontends contain a :class:`Deal` object as state, and provide an
`interact` method as their entry point which allows interactive
manipulation of the deal.
"""

from endplay.interact.frontends.base import BaseFrontend
from endplay.interact.frontends.cmd import CmdFrontend
from endplay.interact.frontends.curses import CursesFrontend
from endplay.interact.frontends.html import HTMLFrontend
