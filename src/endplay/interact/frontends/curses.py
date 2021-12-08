"""
A curses interface to many of the features of endplay including 
dealing hands and performing double-dummy analysis.
"""

__all__ = ["CursesFrontend"]

import curses
from curses.textpad import Textbox, rectangle

class CursesFrontend:
	def __init__(self):
		raise NotImplementedError
		self.command_history = []
		self.ps1 = "> "

	def _main(self, stdscr):
		rows, cols = stdscr.getmaxyx()
		
		# Deal window
		deal_win = curses.newwin(0, 0, 12, 39)

		# DDTable window

		# DDTricks window

		stdscr.hline(12, 0, curses.ACS_HLINE, cols)

		# Command history window
		hist_height = rows - 15
		hist_width = cols
		hist_win = curses.newwin(hist_height, hist_width, 13, cols)

		stdscr.hline(rows - 2, 0, curses.ACS_HLINE, cols)

		# Input window
		stdscr.addstr(rows - 1, 0, self.ps1)
		edit_win = curses.newwin(1, cols - len(self.ps1), rows - 1, len(self.ps1))

		while True:
			stdscr.noutrefresh()
			deal_win.noutrefresh()
			hist_win.noutrefresh()
			edit_win.noutrefresh()
			curses.doupdate()

			csl_in = Textbox(edit_win)
			cmd = csl_in.edit()
			self.command_history.append(cmd)
			for i, h in enumerate(self.command_history[-hist_height::-1]):
				hist_win.addstr(hist_height - i - 1, 0, h)


	def interact(self):
		curses.wrapper(self._main)
