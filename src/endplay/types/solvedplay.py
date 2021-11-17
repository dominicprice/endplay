__all__ = ["SolvedPlay", "SolvedPlayList"]

from typing import Iterator

class SolvedPlay:
	def __init__(self, data: '_dds.solvedPlay'):
		self._data = data

	def __len__(self) -> int:
		":return: The number of results in the play"
		return self._data.number

	def __getitem__(self, i: int) -> int:
		":return: The number of tricks that declarer can make after the ith card is played"
		if i >= len(self):
			raise IndexError
		return self._data.tricks[i]

	def __iter__(self) -> Iterator[int]:
		for i in range(len(self)):
			yield self[i]

	def __repr__(self) -> str:
		return f'<SolvedPlay object; data={self!s}>'

	def __str__(self) -> str:
		return "(" + ", ".join(str(p) for p in self) + ")"

class SolvedPlayList:
	def __init__(self, data: '_dds.solvedPlays'):
		self._data = data

	def __len__(self) -> int:
		":return: The number of boards in the list"
		return self._data.noOfBoards

	def __getitem__(self, i: int) -> SolvedPlay:
		":return: The solved play at index `i`"
		if i >= len(self):
			raise IndexError
		return SolvedPlay(self._data.solved[i])

	def __iter__(self) -> Iterator[SolvedPlay]:
		for i in range(len(self)):
			yield self[i]

	def __repr__(self) -> str:
		return f'<SolvedPlayList; length={len(self)}'

	def __str__(self) -> str:
		return "[" + ", ".join(str(s) for s in self) + "]"