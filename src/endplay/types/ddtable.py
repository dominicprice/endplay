from __future__ import annotations

__all__ = ["DDTableDenom", "DDTable", "DDTableList"]

import sys
import json as _json
from typing import Iterator
from endplay.types.player import Player
from endplay.types.denom import Denom

class DDTable:
	def __init__(self, data: '_dds.ddTableResults'):
		self._data = data
		
	def pprint(self, stream=sys.stdout) -> None:
		"Print the double dummy table in a grid format"
		print("   ", " ".join(denom.abbr.rjust(2) for denom in Denom.bidorder()), file=stream)
		for player in Player.iterorder("NSWE"):
			print(player.abbr.rjust(3), end='', file=stream)
			for denom in Denom.bidorder():
				print(str(self._data.resTable[denom][player]).rjust(3), end='', file=stream)
			print(file=stream)
	
	def to_LaTeX(self) -> str:
		res = r"\begin{tabular}{| c | c  c  c  c c |}"
		res += r"\hline & $\clubsuit$ & $\diamondsuit$ & $\heartsuit$ & $\spadesuit$ & NT \\ \hline "
		for player in Player.iterorder("NSEW"):
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


class DDTableList:
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

	def __iter__(self) -> Iterator[DDTable]:
		for i in range(len(self)):
			yield self[i]

	def __repr__(self) -> str:
		return f'<DDTableList object; length={len(self)}>'

	def __str__(self) -> str:
		if len(self) == 0:
			return "[]"
		return '[(' + "), (".join(str(t) for t in self) + ")]"
