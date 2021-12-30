"""
Solving functions from the DDS library, which calculate the double dummy
results for playing each card in a player's hand.
"""

from __future__ import annotations

__all__ = ["SolvedBoard", "SolvedBoardList", "solve_board", "solve_all_boards"]

from typing import Optional
import endplay._dds as _dds
from endplay.types import Deal, Card, Denom, Rank
from collections.abc import Iterable, Iterator, Sequence

class SolvedBoard(Iterable):
	def __init__(self, data: _dds.solvedBoard):
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

class SolvedBoardList(Sequence):
	def __init__(self, data: _dds.solvedBoards):
			self._data = data

	def __len__(self) -> int:
		":return: The number of boards in the list"
		return self._data.noOfBoards

	def __getitem__(self, i: int) -> SolvedBoard:
		":return: The solved board at index `i`"
		if i < 0:
			i = len(self) - i
		if i < 0 or i >= len(self):
			return IndexError
		return SolvedBoard(self._data.solvedBoard[i])

	def __repr__(self) -> str:
		return f'<SolvedBoardList; length={len(self)}>'

	def __str__(self) -> str:
		if len(self) == 0:
			return "[]"
		return "[(" + ", ".join(str(b) for b in self) + ")]"

def solve_board(deal: Deal, target: Optional[int] = None) -> SolvedBoard:
	"""
	Calculate the double dummy score for all cards in the hand which is currently
	to play in a given deal

	:param deal: The deal to solve, with `first` and `trump` filled in
	:param target: If provided, only return cards which can make at least this many tricks
	"""
	fut = _dds.futureTricks()
	if target is None or target <= 0:
		target, solutions = -1, 3
	else:
		solutions = 2
	_dds.SolveBoard(deal._data, target, solutions, 0, fut, 0)
	return SolvedBoard(fut)

def solve_all_boards(deals: Iterable[Deal], target: Optional[int] = None) -> SolvedBoardList:
	"""
	Optimized version of solve_board for multiple deals which uses threading to
	speed up the calculation

	:param deals: The collection of boards to be solved, each with `first` and `trump` filled
	:param target: If provided, only return cards which can make at least this many tricks
	"""
	# Convert deals into boards
	bop = _dds.boards()
	bop.noOfBoards = 0
	if target is None or target <= 0:
		target, solutions = -1, 3
	else:
		solutions = 2
	for i, deal in enumerate(deals):
		if i > _dds.MAXNOOFBOARDS:
			raise RuntimeError(f"Too many boards, maximum is {_dds.MAXNOOFBOARDS}")
		bop.deals[i] = deal._data
		bop.target[i] = target
		bop.solutions[i] = solutions
		bop.mode[i] = 0
		bop.noOfBoards += 1

	solvedp = _dds.solvedBoards()
	_dds.SolveAllBoardsBin(bop, solvedp)
	return SolvedBoardList(solvedp)