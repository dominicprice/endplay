"""
Par contract and scoring function
"""

from __future__ import annotations

__all__ = ["ParList", "par"]

from typing import Union
import endplay._dds as _dds
from endplay.types import Deal, Contract, Vul, Player
from endplay.dds.ddtable import calc_dd_table, DDTable
from ctypes import pointer
from collections.abc import Iterable, Iterator

class ParList(Iterable):
	def __init__(self, data: '_dds.parResultsMaster'):
		self._data = data

	@property
	def score(self) -> int:
		":return: The score associated with the par contracts"
		return self._data.score

	def __iter__(self) -> Iterator[Contract]:
		":return: An iterator over all the par contracts"
		for i in range(self._data.number):
			c = self._data.contracts[i]
			if c.seats == 4:
				tmp = _dds.contractType()
				pointer(tmp)[0] = c
				c.seats = 0
				yield Contract(c)
				pointer(tmp)[0] = c
				c.seats = 2
				yield Contract(c)
			elif c.seats == 5:
				tmp = _dds.contractType()
				pointer(tmp)[0] = c
				c.seats = 1
				yield Contract(c)
				pointer(tmp)[0] = c
				c.seats = 3
				yield Contract(c)
			else:
				yield Contract(self._data.contracts[i])

	def __repr__(self) -> str:
		return f'<ParList object>'

def par(
	deal: Union[Deal, DDTable], 
	vul: Union[Vul, int], 
	dealer: Player) -> ParList:
	"""
	Calculate the par contract result for the given deal. 

	:param deal: The deal to calculate the par result of. If you have already precomputed a DDTable for
		a deal then you speed up the par calculation by passing that instead of the Deal object
	:param vul: The vulnerability of the deal. If you pass an `int` then this is converted from a board
		number into the vulnerability of that board
	:param dealer: The dealer of the board.
	"""
	if isinstance(deal, Deal):
		dd_table = calc_dd_table(deal)
	else:
		dd_table = deal
	if not isinstance(vul, Vul):
		vul = Vul.from_board(vul)

	par = _dds.parResultsMaster()
	_dds.DealerParBin(dd_table._data, par, dealer, vul)
	return ParList(par)

