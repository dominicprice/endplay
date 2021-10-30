from io import StringIO
from endplay.dealer.actions.base import BaseActions
from endplay.types import Player

class TerminalActions(BaseActions):
	def __init__(self, deals, stream):
		super().__init__(deals, stream)

	def printall(self):
		for deal in self.deals:
			deal.pprint(stream=self.stream)
			print(file=self.stream)

	def print(self, *players):
		exclude = [p for p in Player if p not in players]
		for deal in self.deals:
			deal.pprint(exclude=exclude, stream=self.stream)
			print(file=self.stream)

	def printew(self):
		for deal in self.deals:
			deal.pprint(exclude=[Player.north, Player.south], stream=self.stream)

	def printpbn(self):
		for deal in self.deals:
			print(deal, file=self.stream)

	def printcompact(self, expr = None):
		print(*[p.name.ljust(13) for p in Player], end="\n\n", file=self.stream)
		for deal in self.deals:
			hands = []
			for player in Player:
				buf = StringIO()
				deal[player].pprint(stream=buf)
				hands.append(buf.getvalue().split("\n"))
			if expr is not None:
				hands.append([str(expr(deal)), "", "", ""])
			for line in zip(*hands):
				print(*[s.ljust(13) for s in line], file=self.stream)
			print(file=self.stream)

	def printoneline(self, expr = None):
		for deal in self.deals:
			print(deal.to_pbn()[2:], end=' ', file=self.stream)
			if expr is not None:
				print(expr(deal), file=self.stream)
			else:
				print(file=self.stream)

	def printes(self, *objs):
		for deal in self.deals:
			for obj in objs:
				if callable(obj):
					print(obj(deal), file=self.stream, end='')
				else:
					print(obj, file=self.stream, end='')


	def average(self, expr, s = None):
		total = 0
		for deal in self.deals:
			total += expr(deal)
		if s is not None:
			print(s, end = '', file=self.stream)
		print(total / len(self.deals), file=self.stream)

	def frequency1d(self, expr, lower_bound, upper_bound, s = None):
		import matplotlib.pyplot as plt
		data = [expr(deal) for deal in self.deals]
		plt.hist(data, bins='auto', range=(lower_bound, upper_bound))
		if s:
			plt.title(s)
		plt.show()

	def frequency2d(self, ex1, lb1, hb1, ex2, lb2, hb2, s = None):
		import matplotlib.pyplot as plt
		x = [ex1(deal) for deal in self.deals]
		y = [ex2(deal) for deal in self.deals]
		h = plt.hist2d(x, y, range=[(lb1, hb1), (lb2, hb2)])
		plt.colorbar(h[3])
		if s:
			plt.title(s)
		plt.show()