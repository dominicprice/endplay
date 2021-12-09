"""
Actions class for producing plaintext output.
"""

__all__ = ["TerminalActions"]

from io import StringIO
from endplay.dealer.actions.base import BaseActions
from endplay.types import Player
import endplay.stats as stats

class TerminalActions(BaseActions):
	def __init__(self, deals, stream, board_numbers):
		super().__init__(deals, stream, board_numbers)

	def print(self, *players):
		exclude = [p for p in Player if p not in players]
		for i, deal in enumerate(self.deals, 1):
			deal.pprint(board_no=i if self.board_numbers else None, exclude=exclude, stream=self.stream)
			self.write()

	def printpbn(self):
		for i, deal in enumerate(self.deals, 1):
			if self.board_numbers:
				self.write(str(i).rjust(3), end=' ')
			self.write(str(deal))

	def printcompact(self, expr = None):
		self.write(*[p.name.ljust(13) for p in Player], end="\n\n")
		for i, deal in enumerate(self.deals, 1):
			hands = []
			for player in Player:
				buf = StringIO()
				deal[player].pprint(stream=buf)
				hands.append(buf.getvalue().split("\n"))
			if expr is not None:
				hands.append([str(expr(deal)), "", "", ""])
			if self.board_numbers:
				self.write(str(i) + ")")
			for line in zip(*hands):
				self.write(*[s.ljust(13) for s in line])
			self.write()

	def printoneline(self, expr = None):
		for i, deal in enumerate(self.deals, 1):
			if self.board_numbers:
				self.write(str(i).rjust(3), end=' ')
			self.write(deal.to_pbn()[2:], end=' ')
			if expr is not None:
				self.write(expr(deal))
			else:
				self.write()

	def printes(self, *objs):
		for i, deal in enumerate(self.deals, 1):
			if self.board_numbers:
				self.write(str(i).rjust(3), end=' ')
			for obj in objs:
				if callable(obj):
					self.write(obj(deal), end='')
				else:
					self.write(obj, end='')
			self.write()

	def average(self, expr, s = None):
		if s:
			self.write(s, end="")
		self.write(stats.average(self.deals, expr))

	def frequency1d(self, expr, lb, ub, s = None):
		hist = stats.frequency(self.deals, expr, lb, ub)
		if s:
			self.write(s)
			self.write("=" * len(s))
		rows = [(str(start), str(val)) for start, val in enumerate(hist, lb)]
		lhs_size = max(len(row[0]) for row in rows)
		for row in rows:
			self.write(row[0].rjust(lhs_size), row[1])

	def frequency2d(self, ex1, lb1, ub1, ex2, lb2, ub2, s = None):
		hist = stats.cofrequency(self.deals, ex1, ex2, lb1, ub1, lb2, ub2)
		if s:
			self.write(s)
			self.write("=" * len(s))
		rows = [[""] + [str(i) for i in range(lb2, ub2+1)]]
		for j, row in enumerate(hist, lb1):
			rows += [[str(j) + " |"] + [str(r) for r in row]]
		width = max(max(len(cell) for cell in row) for row in rows)
		self.write(" ".join(c.rjust(width) for c in rows[0]))
		self.write("+".rjust(width) + "-" + "-".join("-"*width for _ in rows[0][1:]))
		for row in rows[1:]:
			self.write(" ".join(c.rjust(width) for c in row))

