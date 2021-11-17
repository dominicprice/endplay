__all__ = ["SuitHolding"]

import ctypes
from endplay.types.denom import Denom
from endplay.types.rank import Rank, AlternateRank
from endplay.types.card import Card
from typing import Iterable, Iterator, Optional, Union

class SuitHolding:
	def __init__(self, data: Union[ctypes.c_uint * 4, str] = "", idx: Optional[int] = None):
		"""
		Construct a suit holding
		:param data: A PBN string representation of the holding or a reference to a _dds object
		"""
		if isinstance(data, str):
			self._data = (ctypes.c_uint * 4)(0,0,0,0)
			self._idx = 0
			self.from_pbn(data)
		else:
			if idx is None:
				raise ValueError("No index given to SuitHolding")
			self._idx = idx
			self._data = data

	def __copy__(self) -> 'SuitHolding':
		return SuitHolding((ctypes.c_uint * 4).from_buffer_copy(self._data), self._idx)

	def copy(self) -> 'SuitHolding':
		return self.__copy__()
	
	def add(self, rank: Rank) -> bool:
		"""
		Add a rank to the suit holding
		:param rank: The rank to add
		:return: False if the rank was already in the holding, True otherwise
		"""
		if isinstance(rank, str):
			rank = Rank.find(rank)
		if isinstance(rank, AlternateRank):
			rank = rank.to_standard()
		if rank in self:
			return False
		self._data[self._idx] |= rank.value
		return True
		
	def extend(self, ranks: Iterable[Rank]) -> int:
		"""
		Add multiple ranks to the suit holding
		:parm ranks: An iterable of the ranks to add
		:return: The number of ranks successfully added
		"""
		return sum(self.add(rank) for rank in ranks)

	def remove(self, rank: Rank) -> bool:
		"""
		Remove a rank from the suit holding
		:param rank: The rank to remove
		:return: False if the rank wasn't in the holding, True otherwise
		"""
		if isinstance(rank, str):
			rank = Rank.find(rank)
		if isinstance(rank, AlternateRank):
			rank = rank.to_standard()
		if not rank in self:
			return False
		self._data[self._idx] &= ~rank.value
		return True

	def clear(self) -> None:
		"""
		Removes all cards from the holding
		"""
		self._data[self._idx] = 0

	def to_pbn(self) -> str:
		return "".join(rank.abbr for rank in self)

	def from_pbn(self, pbn: str) -> None:
		self.clear()
		for rank in pbn:
			self.add(rank)

	def __eq__(self, other: 'SuitHolding') -> bool:
		if len(self) != len(other):
			return False
		for a, b in zip(self, other):
			if a != b:
				return False
		return True

	def __contains__(self, rank: Rank) -> bool:
		if isinstance(rank, str):
			rank = Rank.find(rank)
		if isinstance(rank, AlternateRank):
			rank = rank.to_standard()
		return self._data[self._idx] & rank.value

	def __iter__(self) -> Iterator[Rank]:
		for rank in reversed(Rank):
			if rank in self: yield rank
		
	def __reversed__(self) -> Iterator[Rank]:
		for rank in Rank:
			if rank in self: yield rank

	def __len__(self) -> int:
		n = self._data[self._idx]
		b = bin(n)
		return b.count('1')

	def __str__(self) -> str:
		return self.to_pbn()

	def __repr__(self) -> str:
		return f'SuitHolding("{self!s}")'