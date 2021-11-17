__all__ = ["solve_board", "solve_all_boards"]

from typing import Iterable, Optional
import endplay._dds as _dds
from endplay.types import Deal, SolvedBoard, SolvedBoardList

def solve_board(deal: Deal, target: Optional[int] = None) -> SolvedBoard:
	"""
	Calculate the double dummy score for all cards in the hand which is currently
	to play in a given deal
	:param deal: The deal to solve, with `first` and `trump` filled int
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