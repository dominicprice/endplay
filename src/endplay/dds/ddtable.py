"""
Double dummy table calculation functions
"""

from __future__ import annotations

__all__ = ["DDTable", "DDTableList", "calc_dd_table", "calc_all_tables"]

import sys
import json as _json
from collections import abc
from collections.abc import Iterable
import endplay._dds as _dds
from endplay.types import Deal, Denom, Player

class DDTable:
	def __init__(self, data: '_dds.ddTableResults'):
		self._data = data
		
	def pprint(self, stream=sys.stdout) -> None:
		"Print the double dummy table in a grid format"
		print("   ", " ".join(denom.abbr.rjust(2) for denom in Denom.bidorder()), file=stream)
		for player in Player.iter_order("NSWE"):
			print(player.abbr.rjust(3), end='', file=stream)
			for denom in Denom.bidorder():
				print(str(self._data.resTable[denom][player]).rjust(3), end='', file=stream)
			print(file=stream)
	
	def to_LaTeX(self) -> str:
		res = r"\begin{tabular}{| c | c  c  c  c c |}"
		res += r"\hline & $\clubsuit$ & $\diamondsuit$ & $\heartsuit$ & $\spadesuit$ & NT \\ \hline "
		for player in Player.iter_order("NSEW"):
			res += player.abbr + " & " + " & ".join(str(self[denom][player]) for denom in Denom.bidorder()) + "\\\\"
		res += r"\hline \end{tabular}"
		return res

	def to_json(self) -> str:
		return _json.dumps({ { p.name: self[d][p] for p in Player } for d in Denom })

	def __getitem__(self, cell: tuple[Denom, Player]) -> int:
		"Return the specified column of the table"
		if isinstance(cell[0], Denom):
			return self._data.resTable[cell[0]][cell[1]]
		else:
			return self._data.resTable[cell[1]][cell[0]]

	def __repr__(self) -> str:
		return f'<DDTable object; data={self!s}>'

	def __str__(self) -> str:
		return ", ".join(f"{denom.abbr}:{{{self[denom]}}}" for denom in Denom.bidorder())

class DDTableList(abc.Sequence):
	def __init__(self, data: '_dds.ddTableRes'):
		self._data = data

	def __len__(self) -> int:
		"The number of double dummy tables in the list"
		return self._data.noOfBoards

	def __getitem__(self, i: int) -> DDTable:
		"Return the double dummy table at index `i`"
		if i >= len(self):
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