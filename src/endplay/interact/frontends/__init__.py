"""
Frontends contain a :class:`Deal` object as state, and provide an
`interact` method as their entry point which allows interactive
manipulation of the deal.
"""

from endplay.interact.frontends.cmd import CmdFrontend
from endplay.interact.frontends.curses import CursesFrontend
from endplay.interact.frontends.tk import TkFrontend