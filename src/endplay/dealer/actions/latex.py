"""
Actions class for producing LaTeX output.
"""

__all__ = ["LateXActions"]

from endplay.dealer.actions.base import BaseActions
from endplay.types import Denom, Player
from io import StringIO
import endplay.stats as stats
import matplotlib.pyplot as plt

class LaTeXActions(BaseActions):
	def __init__(self, deals, stream, board_numbers):
		super().__init__(deals, stream, board_numbers, "tex")

	def print(self, *players):
		exclude = [p for p in Player if p not in players]
		self.write(r"\noindent ")
		for deal in self.deals:
			self.write(r"\resizebox{0.33\textwidth}{!}{" + deal.to_LaTeX(exclude=exclude) + "}")

	def printpbn(self):
		for deal in self.deals:
			self.write(str(deal))

	def printcompact(self, expr = None):
		if expr is None:
			expr = lambda deal: ""
		for deal in self.deals:
			self.write(r"\begin{tabular}{l | l | l | l | l | l}")
			self.write(r"& \textbf{North} & \textbf{East} & \textbf{South} & \textbf{West} & \textbf{Value} \\ \hline")
			self.write(r"$\spadesuit$ &", " & ".join(str(deal[p][Denom.spades]) for p in Player), r"& \\ ")
			self.write(r"$\heartsuit$ &", " & ".join(str(deal[p][Denom.hearts]) for p in Player), "&", expr(deal), r"\\ ")
			self.write(r"$\diamondsuit$ &", " & ".join(str(deal[p][Denom.diamonds]) for p in Player), r"& \\ ")
			self.write(r"$\clubsuit$ &", " & ".join(str(deal[p][Denom.clubs]) for p in Player), r"& \\ ")
			self.write(r"\end{tabular} \\ ")

	def printoneline(self, expr = None):
		for deal in self.deals:
			for player in Player:
				self.write(player.abbr, end=":")
				for denom in Denom.suits():
					self.write("$\\" + denom.name + "uit$" + str(deal[player][denom]), end=' ')
			if expr is not None:
				self.write(f" [{expr(deal)}]", end=' ')
			self.write(r"\\ ")

	def printes(self, *objs):
		for deal in self.deals:
			for obj in objs:
				if callable(obj):
					self.write(obj(deal), end='')
				else:
					self.write(obj, end='')

	def average(self, expr, s = None):
		if s:
			self.write(s, end="")
		self.write(stats.average(self.deals, expr))

	@staticmethod
	def mpl_init_pgf():
		import matplotlib
		matplotlib.use("pgf")
		matplotlib.rcParams.update({
			"pgf.texsystem": "pdflatex",
			'font.family': 'serif',
			'text.usetex': True,
			'pgf.rcfonts': False,
		})

	def frequency1d(self, expr, lb, ub, s = None):
		LaTeXActions.mpl_init_pgf()
		hist = stats.frequency(self.deals, expr, lb, ub)
		fig, ax = plt.subplots()
		ax.bar(list(range(lb, ub+1)), hist)
		if s: ax.set_title(s)
		f = StringIO()
		fig.savefig(f, format="pgf")
		self.write(f.getvalue())

	def frequency2d(self, ex1, lb1, ub1, ex2, lb2, ub2, s = None):
		LaTeXActions.mpl_init_pgf()
		hist = stats.cofrequency(self.deals, ex1, ex2, lb1, ub1, lb2, ub2)
		fig, ax = plt.subplots()
		m = ax.matshow(hist)
		fig.colorbar(m)
		ax.set_xticks(list(range(1 + ub2 - lb2)))
		ax.set_xticklabels([str(i) for i in range(lb2, ub2+1)])
		ax.set_yticks(list(range(1 + ub1 - lb1)))
		ax.set_yticklabels([str(i) for i in range(lb1, ub1+1)])
		if s: ax.set_title(s)
		f = StringIO()
		fig.delaxes(fig.get_axes()[1]) # fixme: currently don't support colorbar in latex
		fig.savefig(f, format="pgf")
		self.write(f.getvalue())