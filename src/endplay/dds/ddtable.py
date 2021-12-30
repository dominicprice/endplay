"""
Double dummy table calculation functions
"""

from __future__ import annotations

__all__ = ["DDTable", "DDTableList", "calc_dd_table", "calc_all_tables"]

import sys
from collections import abc
from collections.abc import Iterable
import endplay._dds as _dds
from endplay.types import Deal, Denom, Player

class DDTable:
	"""
	Python wrapper for the `_dds.ddTableResults` class. Entries can be accessed
	using the `__getitem__` operator e.g. table[Denom.clubs, Player.west]
	"""
	def __init__(self, data: _dds.ddTableResults):
		self._data = data
		
	def pprint(self, 
		*, 
		denoms: Iterable[Denom] = [Denom.clubs, Denom.diamonds, Denom.hearts, Denom.spades, Denom.nt],
		players: Iterable[Player] = [Player.north, Player.south, Player.east, Player.west],
		stream=sys.stdout) -> None:
		"""
		Print the double dummy table in a grid format
		
		:param denoms: Specify the columns of the table
		:param players: Specify the rows of the table
		"""
		denoms, players = list(denoms), list(players)
		print("   ", " ".join(denom.abbr.rjust(2) for denom in denoms), file=stream)
		for player in players:
			print(player.abbr.rjust(3), end='', file=stream)
			for denom in denoms:
				print(str(self[denom, player]).rjust(3), end='', file=stream)
			print(file=stream)
	
	def to_LaTeX(self) -> str:
		"""Create a LaTeX string of the table"""
		res = r"\begin{tabular}{| c | c  c  c  c c |}"
		res += r"\hline & $\clubsuit$ & $\diamondsuit$ & $\heartsuit$ & $\spadesuit$ & NT \\ \hline "
		for player in Player.iter_order("NSEW"):
			res += player.abbr + " & " + " & ".join(str(self[denom][player]) for denom in Denom.bidorder()) + "\\\\"
		res += r"\hline \end{tabular}"
		return res

	def to_list(self, player_major: bool = False) -> list[list[int]]:
		"""
		Convert the table to a 2d list

		:param player_major: If `True`, the returned list is index by player first then strain
		"""
		if player_major:
			return [[self[d, p] for d in Denom] for p in Player]
		else:
			return [[self[d, p] for p in Player] for d in Denom]

	def __getitem__(self, cell: tuple[Denom, Player]) -> int:
		"""Return the specified cell of the table"""
		if isinstance(cell[0], Denom):
			return self._data.resTable[cell[0]][cell[1]]
		else:
			return self._data.resTable[cell[1]][cell[0]]

	def __str__(self) -> str:
		return ",".join(d.abbr for d in Denom.bidorder()) + \
			";" + ";".join(p.abbr + ":" + \
			",".join(str(self[d, p]) for d in Denom.bidorder()) for p in Player)

class DDTableList(abc.Sequence):
	def __init__(self, data: '_dds.ddTableRes'):
		self._data = data

	def __len__(self) -> int:
		"The number of double dummy tables in the list"
		return self._data.noOfBoards

	def __getitem__(self, i: int) -> DDTable:
		"Return the double dummy table at index `i`"
		if i < 0:
			i = len(self) - i
		if i < 0 or i >= len(self):
			raise IndexError
		return DDTable(self._data.results[i])

	def __repr__(self) -> str:
		return f'<DDTableList object; length={len(self)}>'

	def __str__(self) -> str:
		if len(self) == 0:
			return "[]"
		return '[(' + "), (".join(str(t) for t in self) + ")]"

def calc_dd_table(deal: Deal) -> DDTable:
	"""
	Calculates the double dummy results for all 20 possible combinations of
	dealer and trump suit for a given deal
	"""
	# Convert deal into ddTableDeal
	dl = _dds.ddTableDeal()
	dl.cards = deal._data.remainCards

	table =_dds.ddTableResults()
	_dds.CalcDDtable(dl, table)
	return DDTable(table)

def calc_all_tables(deals: Iterable[Deal], exclude: Iterable[Denom] = []) -> DDTableList:
	"""
	Optimized version of calc_dd_table for multiple deals which uses threading to
	speed up the calculation. `exclude` can contain a list of denominations to
	exclude from the calculation, e.g. if only the notrump results for the deals
	is required then pass `Denom.suits()` 
	"""
	# Convert deals to ddTableDeals
	dealsp = _dds.ddTableDeals()
	dealsp.noOfTables = 0
	for i, deal in enumerate(deals):
		if i > _dds.MAXNOOFTABLES * 5:
			raise RuntimeError(f"Too many boards, maximum is {_dds.MAXNOOFTABLES * 5}")
		dealsp.ddTableDeal[i].cards = deal._data.remainCards
		dealsp.noOfTables += 1

	# Convert exclude to a trump filter list
	trumpFilter = [False]*5
	for trump in exclude:
		trumpFilter[trump] = True

	resp = _dds.ddTablesRes()
	presp = _dds.allParResults()
	_dds.CalcAllTables(dealsp, -1, trumpFilter, resp, presp)
	resp.noOfBoards = dealsp.noOfTables
	return DDTableList(resp)