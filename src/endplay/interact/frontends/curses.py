"""
A curses interface to many of the features of endplay including
dealing hands and performing double-dummy analysis.
"""

__all__ = ["CursesFrontend"]

import curses
import io
import shlex
import textwrap
from curses.textpad import Textbox
from typing import Optional

from endplay.dds.ddtable import calc_dd_table
from endplay.dds.solve import solve_board
from endplay.evaluate import hcp
from endplay.interact.commandobject import CommandObject
from endplay.interact.frontends.base import BaseFrontend
from endplay.types.denom import Denom
from endplay.types.player import Player


def addcstr(win: "curses._CursesWindow", y: int, x: int, s: str):
    for i, c in enumerate(s, x):
        if c == Denom.spades.abbr:
            win.addch(y, i, c, curses.color_pair(3))
        elif c == Denom.hearts.abbr:
            win.addch(y, i, c, curses.color_pair(4))
        elif c == Denom.diamonds.abbr:
            win.addch(y, i, c, curses.color_pair(5))
        elif c == Denom.clubs.abbr:
            win.addch(y, i, c, curses.color_pair(6))
        else:
            win.addch(y, i, c)


class CursesFrontend(BaseFrontend):
    dealwin: "curses._CursesWindow"
    trickswin: "curses._CursesWindow"
    infowin: "curses._CursesWindow"
    tablewin: "curses._CursesWindow"
    hcpwin: "curses._CursesWindow"
    inputwin: "curses._CursesWindow"
    consolewin: "curses._CursesWindow"

    def __init__(self, cmdobj: CommandObject):
        self.cmdobj = cmdobj
        self.command = ""
        self._ps1 = "{onlead}> "
        self.console_lines: list[tuple[str, Optional[str], bool]] = []

    @property
    def ps1(self):
        return self._ps1.format(onlead=self.cmdobj.deal.curplayer.abbr)

    def initialise(self, stdscr: "curses._CursesWindow"):
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_WHITE)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_WHITE)
        curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_WHITE)
        curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_WHITE)

        rows, cols = stdscr.getmaxyx()

        # left column
        self.dealwin = curses.newwin(14, 42, 1, 2)
        self.infowin = curses.newwin(3, 42, 16, 2)
        self.trickswin = curses.newwin(5, 42, 20, 2)
        self.tablewin = curses.newwin(8, 23, 26, 2)
        self.hcpwin = curses.newwin(8, 17, 26, 27)

        # right column
        self.consolewin = curses.newwin(rows - 4, cols - 48, 1, 46)
        self.inputwin = curses.newwin(2, cols - 48, rows - 3, 46)

        self.dealwin.bkgd(" ", curses.color_pair(2))
        self.infowin.bkgd(" ", curses.color_pair(1))
        self.trickswin.bkgd(" ", curses.color_pair(1))
        self.tablewin.bkgd(" ", curses.color_pair(1))
        self.hcpwin.bkgd(" ", curses.color_pair(1))
        self.consolewin.bkgd(" ", curses.color_pair(1))
        self.inputwin.bkgd(" ", curses.color_pair(1))

    def update(self):
        self.dealwin.erase()
        self.infowin.erase()
        self.trickswin.erase()
        self.tablewin.erase()
        self.hcpwin.erase()
        self.inputwin.erase()
        self.consolewin.erase()

        # update deal
        stream = io.StringIO()
        self.cmdobj.deal.pprint(stream=stream, board_no=self.cmdobj.board)
        for i, line in enumerate(stream.getvalue().splitlines()):
            self.dealwin.addstr(i + 1, 2, line)

        # update info
        addcstr(
            self.infowin,
            1,
            2,
            f"Playing in {self.cmdobj.deal.trump.abbr}, {self.cmdobj.deal.first.abbr} leading this trick",
        )

        # update tricks
        self.trickswin.addstr(1, 2, "Tricks:")
        try:
            sols = solve_board(self.cmdobj.deal)
            cards = "".join([str(sol[0]).ljust(3) for sol in sols])
            tricks = "".join([str(sol[1]).ljust(3) for sol in sols])
            addcstr(self.trickswin, 2, 2, cards)
            self.trickswin.addstr(3, 2, tricks)
        except Exception as e:
            self.trickswin.addstr(2, 2, str(e))

        # update ddtable
        self.tablewin.addstr(1, 2, "DD Table:")
        try:
            if len(self.cmdobj.deal[Player.north]) == 0:
                raise RuntimeError("Zero cards")
            table = calc_dd_table(self.cmdobj.deal)
            stream = io.StringIO()
            table.pprint(stream=stream)
            for i, line in enumerate(stream.getvalue().splitlines()):
                addcstr(self.tablewin, i + 2, 2, line)
        except Exception as e:
            self.tablewin.addstr(2, 2, str(e))

        # update hcp
        self.hcpwin.addstr(1, 2, "HCP:")
        self.hcpwin.addstr(2, 8, str(hcp(self.cmdobj.deal.north)))
        self.hcpwin.addstr(4, 4, str(hcp(self.cmdobj.deal.west)))
        self.hcpwin.addstr(4, 12, str(hcp(self.cmdobj.deal.east)))
        self.hcpwin.addstr(6, 8, str(hcp(self.cmdobj.deal.south)))

        # history
        max_lines, max_cols = self.consolewin.getmaxyx()
        max_lines -= 1
        max_cols -= 5
        output: list[tuple[str, int]] = []
        for i, cmd in enumerate(reversed(self.console_lines)):
            lines_remaining = max_lines - len(output)
            if lines_remaining <= 0:
                break

            cmd_output = [
                (f"[{len(self.console_lines) - i}] {cmd[0]}", curses.color_pair(3))
            ]
            if cmd[1] is not None:
                c = curses.color_pair(4) if cmd[2] else curses.color_pair(1)
                for l in cmd[1].splitlines():
                    for splitl in textwrap.fill(l, max_cols).splitlines():
                        cmd_output += [(splitl, c)]
            if len(cmd_output) > lines_remaining:
                cmd_output = cmd_output[len(cmd_output) - lines_remaining :]
            output = cmd_output + output

        start_line = max_lines - len(output)
        for i, (line, color) in enumerate(output, start_line):
            self.consolewin.addstr(i + 1, 2, line, color)

        # input field
        _, input_cols = self.inputwin.getmaxyx()
        self.inputwin.hline(curses.ACS_HLINE, input_cols)
        self.inputwin.addstr(1, 2, self.ps1, curses.color_pair(3))

        self.dealwin.noutrefresh()
        self.infowin.noutrefresh()
        self.trickswin.noutrefresh()
        self.tablewin.noutrefresh()
        self.hcpwin.noutrefresh()
        self.inputwin.noutrefresh()
        self.consolewin.noutrefresh()
        curses.doupdate()

    def process_input(self):
        begy, begx = self.inputwin.getbegyx()
        _, maxx = self.inputwin.getmaxyx()
        editwin = curses.newwin(
            1, maxx - 2 - len(self.ps1), begy + 1, begx + 2 + len(self.ps1)
        )
        editwin.bkgd(curses.color_pair(3))
        textbox = Textbox(editwin)
        textbox.edit()
        self.command = textbox.gather()
        self.dispatch_command()

    def main(self, stdscr: "curses._CursesWindow"):
        self.initialise(stdscr)
        stdscr.noutrefresh()
        while True:
            self.update()
            self.process_input()

    def interact(self):
        curses.wrapper(self.main)

    def dispatch_command(self):
        if self.command.strip() == "":
            return

        cmdline = self.command
        self.command = ""

        try:
            output, error = self.cmdobj.dispatch(shlex.split(cmdline)), False
        except Exception as e:
            output, error = "error: " + str(e), True

        self.console_lines += [(cmdline, output, error)]
