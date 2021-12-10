"""
Actions class for producing HTML output
"""

__all__ = ["HTMLActions"]

from endplay.dealer.actions.base import BaseActions
from endplay.types import Denom, Player, Vul
from io import StringIO
import endplay.stats as stats
import matplotlib.pyplot as plt

class HTMLActions(BaseActions):
	def __init__(self, deals, stream, board_numbers):
		super().__init__(deals, stream, board_numbers, "html")
#
	def print(self, *players):
		compass = '<div class="compass">'
		for player in Player.iter_order("NWES"):
			compass += f'<div class="{player.name}">{player.abbr}</div>'
		compass += "</div>"
		box = "<div></div>"
		self.write("<div>")
		for i, deal in enumerate(self.deals, 1):
			if self.board_numbers:
				info = f'<div class="board-info"><div>Board {i}</div>'
				info += f'<div>Vul {Vul.from_board(i).abbr}</div><div>'
				info += f'{Player((i-1) % 4).abbr} deals</div></div>'
			else:
				info = box
			hands = {}
			for player in Player:
				if player in players:
					h = f'<div class="hand {player.name}">'
					for denom in Denom.suits():
						holding = str(deal[player][denom]) or "&mdash;"
						h += f'<div class="{denom.name}">{holding}</div>'
					hands[player] = h + "</div>"
				else:
					hands[player] = r'<div class="hand {player.name}"></div>'
			self.write('<div class="deal" style="margin: 20px">')
			self.write(
				info, hands[Player.north], box, 
				hands[Player.west], compass, hands[Player.east],
				box, hands[Player.south], box)
			self.write('</div>')
		self.write("</div>")

	def printpbn(self):
		self.write('<table class="deal-oneline">')
		self.write('<tr>', end='')
		if self.board_numbers:
			self.write('<th>#</th>', end='')
		self.write('<th>PBN</th>', end='')
		self.write("</tr>")
		for i, deal in enumerate(self.deals, 1):
			self.write('<tr>', end='')
			if self.board_numbers:
				self.write(f'<td><div class="value">{i}</div></td>', end='')
			self.write(f'<td><div class="hand-inline">{str(deal)}</div></td>')
			self.write('</tr>')
		self.write('</table>')

	def printcompact(self, expr = None):
		self.write('<table class="deal-compact">')
		self.write('<tr>')
		if self.board_numbers:
			self.write('<th>#</th>')
		self.write('<th>North</th><th>East</th><th>South</th><th>West</th>', end='')
		if expr is not None:
			self.write('<th>Value</th>', end='')
		self.write("</tr>")
		for i, deal in enumerate(self.deals, 1):
			self.write("<tr>")
			if self.board_numbers:
				self.write(f'<td><div class="value">{i}</div></td>', end='')
			for player in Player:
				self.write('<td><div class="hand">')
				for denom in Denom.suits():
					holding = str(deal[player][denom]) or "&mdash;"
					self.write(f'<div class="{denom.name}">{holding}</div>')
				self.write('</div></td>')
			if expr is not None:
				self.write(f'<td><div class="value">{expr(deal)}</div></td>')
			self.write('</tr>')
		self.write('</table>')
		
	def printoneline(self, expr = None):
		self.write('<table class="deal-oneline">')
		self.write('<tr>', end='')
		if self.board_numbers:
			self.write('<th>#</th>', end='')
		self.write('<th>North</th><th>East</th><th>South</th><th>West</th>', end='')
		if expr is not None:
			self.write('<th>Value</th>', end='')
		self.write("</tr>")
		for i, deal in enumerate(self.deals, 1):
			self.write("<tr>")
			if self.board_numbers:
				self.write(f'<td><div class="value">{i}</div></td>', end='')
			for player in Player:
				self.write('<td><div class="hand-inline">')
				for denom in Denom.suits():
					holding = str(deal[player][denom]) or "&mdash;"
					self.write(f'<div class="{denom.name} inline">{holding}</div>')
				self.write('</div></td>')
			if expr is not None:
				self.write(f'<td><div class="value">{expr(deal)}</div></td>')
			self.write('</tr>')
		self.write('</table>')

	def printes(self, *objs):
		self.write('<table class="deal-oneline">')
		self.write('<tr>', end='')
		if self.board_numbers:
			self.write('<th>#</th>', end='')
		self.write('<th>Output</th>', end='')
		self.write("</tr>")
		for i, deal in enumerate(self.deals, 1):
			self.write('<tr>', end='')
			if self.board_numbers:
				self.write(f'<td><div class="value">{i}</div></td>', end='')
			self.write(f'<td><div class="value">')
			for obj in objs:
				if callable(obj):
					self.write(obj(deal), end='')
				else:
					self.write(str(obj).replace('\n', "<br>"), end='')
			self.write(f'</div></td>')
			self.write('</tr>')
		self.write('</table>')

	def average(self, expr, s = None):
		if s is None:
			s = ""
		self.write('<div class="valuebox">', s, stats.average(self.deals, expr), "</div>")

	def frequency1d(self, expr, lb, ub, s = None):
		hist = stats.frequency(self.deals, expr, lb, ub)
		fig, ax = plt.subplots()
		ax.bar(list(range(lb, ub+1)), hist)
		if s: ax.set_title(s)
		f = StringIO()
		fig.savefig(f, format="svg")
		self.write('<div class="valuebox">', f.getvalue(), "</div>")

	def frequency2d(self, ex1, lb1, ub1, ex2, lb2, ub2, s = None):
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
		fig.savefig(f, format="svg")
		self.write('<div class="valuebox">', f.getvalue(), "</div>")