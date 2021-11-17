from __future__ import annotations

__all__ = ["SolvedBoard", "SolvedBoardList"]

from endplay.types.card import Card
from endplay.types.denom import Denom
from endplay.types.rank import Rank
from typing import Iterator

class SolvedBoard:
	def __init__(self, data: '_dds.solvedBoard'):
		self._data = data

	def __iter__(self) -> Iterator[tuple[Card, int]]:
		":return: An iterator of (card, maxTrick) pairs"
		for i in range(self._data.cards):
			if self._data.score[i] == -1:
				continue
			holding = (1 << self._data.rank[i]) | self._data.equals[i]
			for rank in Rank:
				if holding & rank.value:
					card = Card(suit=Denom(self._data.suit[i]), rank=rank)
					yield (card, self._data.score[i])

	def __repr__(self) -> str:
		return f'<SolvedBoard object>'

	def __str__(self) -> str:
		return '{' + ", ".join("b[0]:b[1]" for b in self) + '}'

class SolvedBoardList:
	def __init__(self, data: '_dds.solvedBoards'):
			self._data = data

	def __len__(self) -> int:
		":return: The number of boards in the list"
		return self._data.noOfBoards

	def __getitem__(self, i: int) -> SolvedBoard:
		":return: The solved board at index `i`"
		if i >= len(self):
			return IndexError
		return SolvedBoard(self._data.solvedBoard[i])

	def __iter__(self) -> Iterator[SolvedBoard]:
		for i in range(len(self)):
			yield self[i]

	def __repr__(self) -> str:
		return f'<SolvedBoardList; length={len(self)}>'

	def __str__(self) -> str:
		if len(self) == 0:
			return "[]"
		return "[(" + ", ".join(str(b) for b in self) + ")]"