__all__ = ["DDTableDenom", "DDTable", "DDTableList"]

import sys
import json as _json
from endplay.types.player import Player
from endplay.types.denom import Denom

class DDTableDenom:
	def __init__(self, data: 'ctypes.c_int * 4'):
		self._data = data
		
	def __getitem__(self, player: Player) -> int:
		"Return the specified cell of the table"
		return self._data[player]

	def __setitem__(self, player: Player, val: int) -> None:
		"Modify the specified cell of the table"
		self._data[player] = val

	def __repr__(self) -> str:
		return '<DDTableDenom object; data={{{self!s}}}>'

	def __str__(self) -> str:
		return ",".join("{player.abbr}:{self[player]}" for player in Player)

class DDTable:
	def __init__(self, data: '_dds.ddTableResults'):
		self._data = data
		
	def pprint(self, stream=sys.stdout) -> None:
		"Print the double dummy table in a grid format"
		print("    ", " ".join(denom.abbr.rjust(2) for denom in Denom.bidorder()), file=stream)
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

	def __getitem__(self, denom: Denom) -> DDTableDenom:
		"Return the specified column of the table"
		return DDTableDenom(self._data.resTable[denom.value])

	def __repr__(self) -> str:
		return f'<DDTable object; data={self!s}>'

	def __str__(self) -> str:
		", ".join("{denom.abbr}:{{{self[denom]}}" for denom in Denom.bidorder())


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

	def __repr__(self) -> str:
		return f'<DDTableList object; length={len(self)}>'

	def __str__(self) -> str:
		if len(self) == 0:
			return "[]"
		return '[(' + "), (".join(str(t) for t in self) + ")]"
