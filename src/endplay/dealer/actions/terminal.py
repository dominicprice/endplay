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

	def frequency1d(self, expr, lower_bound, upper_bound, s = None):
		counts, bins, fig = stats.histogram(self.deals, expr, lower_bound, upper_bound)
		fig.get_axes()[0].set_title(s)
		fig.show()

	def frequency2d(self, ex1, lb1, hb1, ex2, lb2, hb2, s = None):
		import matplotlib.pyplot as plt
		counts, bins, fig = stats.histogram2d(self.deals, (ex1, ex2), (lb1, lb2), (hb1, hb2))
		fig.get_axes()[0].set_title(s)
		plt.show()