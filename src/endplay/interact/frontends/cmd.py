"""
A shell-like interface to many of the features of endplay including 
dealing hands and performing double-dummy analysis.
"""

__all__ = ["CmdFrontend"]

import shlex

from endplay.interact.commandobject import CommandObject
from endplay.interact.frontends.base import BaseFrontend


class CmdFrontend(BaseFrontend):
    def __init__(self, cmdobj: CommandObject):
        self.cmdobj = cmdobj
        self._ps1 = "{onlead}> "

    @property
    def ps1(self):
        return self._ps1.format(onlead=self.cmdobj.deal.curplayer.abbr)

    def interact(self):
        print("endplay interactive deal analyser, type help for more info.")
        display = True
        while True:
            print()
            if display:
                self.cmdobj.deal.pprint(self.cmdobj.board)

            cmd = input(self.ps1)
            if cmd.strip() == "":
                display = False
                continue

            cmdline = shlex.split(cmd)
            output = self.cmdobj.dispatch(cmdline)
            if output is not None:
                print(output)
            display = True
