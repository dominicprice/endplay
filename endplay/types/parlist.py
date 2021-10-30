__all__ = ["ParList"]

import endplay._dds as _dds
from endplay.types import Contract
from typing import Iterator
from ctypes import pointer

class ParList:
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