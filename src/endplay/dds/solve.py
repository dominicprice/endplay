"""
Solving functions from the DDS library, which calculate the double dummy
results for playing each card in a player's hand.
"""

from __future__ import annotations

from enum import IntEnum

__all__ = ["SolvedBoard", "SolvedBoardList", "solve_board", "solve_all_boards"]

from collections.abc import Iterable, Iterator, Sequence
from typing import Optional, Union, overload

import endplay._dds as _dds
from endplay.types import Card, Deal, Denom, Rank


class SolveMode(IntEnum):
    "Returns all cards that can be legally played with their scores"
    Default = 0

    "Returns one card which produces the maximum number of tricks"
    OptimalOne = 1

    "Returns all cards which produce the maximum number of tricks"
    OptimalAll = 2

    "Returns one card which is legal to play, with score set to zero"
    LegalOne = 3

    "Returns all cards which are legal to play, with score set to zero"
    LegalAll = 4

    """
    Returns one card with the score set to -1 if the target could not
    be reached, 0 if no tricks can be won or the given target if it
    can be reached
    """
    TargetOne = 5

    """
    Returns all cards which meet the target, or a single card with the
    score set to -1 if the target could not be reached
    """
    TargetAll = 6

    def target_solutions(self, target: Optional[int] = None) -> tuple[int, int]:
        if self == SolveMode.Default:
            return 0, 3
        elif self == SolveMode.OptimalOne:
            return -1, 1
        elif self == SolveMode.OptimalAll:
            return -1, 2
        elif self == SolveMode.LegalOne:
            return 0, 1
        elif self == SolveMode.LegalAll:
            return 0, 2
        elif self == SolveMode.TargetOne:
            if target is None or target < 1:
                raise RuntimeError("target must be >= 1 for this solve mode")
            return target, 1
        elif self == SolveMode.TargetAll:
            if target is None or target < 1:
                raise RuntimeError("target must be >= 1 for this solve mode")
            return target, 2
        else:
            raise RuntimeError(f"unknown solve mode {self}")


class SolvedBoard(Iterable):
    def __init__(self, data: _dds.futureTricks):
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
        return "<SolvedBoard object>"

    def __str__(self) -> str:
        return "{" + ", ".join(f"{b[0]}:{b[1]}" for b in self) + "}"


class SolvedBoardList(Sequence):
    def __init__(self, data: _dds.solvedBoards):
        self._data = data

    def __len__(self) -> int:
        ":return: The number of boards in the list"
        return self._data.noOfBoards

    @overload
    def __getitem__(self, i: int) -> SolvedBoard:
        ...

    @overload
    def __getitem__(self, i: slice) -> Sequence[SolvedBoard]:
        ...

    def __getitem__(
        self, i: Union[int, slice]
    ) -> Union[SolvedBoard, Sequence[SolvedBoard]]:
        ":return: The solved board at index `i`"
        if isinstance(i, int):
            if i < 0:
                i = len(self) - i
            if i < 0 or i >= len(self):
                raise IndexError
            return SolvedBoard(self._data.solvedBoard[i])
        else:
            return [self[ii] for ii in range(*i.indices(len(self)))]

    def __repr__(self) -> str:
        return f"<SolvedBoardList; length={len(self)}>"

    def __str__(self) -> str:
        if len(self) == 0:
            return "[]"
        return "[(" + ", ".join(str(b) for b in self) + ")]"


def solve_board(
    deal: Deal,
    mode: SolveMode = SolveMode.Default,
    target: Optional[int] = None,
) -> SolvedBoard:
    """
    Calculate the double dummy score for all cards in the hand which is currently
    to play in a given deal

    :param deal: The deal to solve, with `first` and `trump` filled in
    :param target: If provided, only return cards which can make at least this many tricks. Ignored
    unless `SolveMode` is set to `TargetOne` or `TargetAll`
    """
    fut = _dds.futureTricks()
    target, solutions = mode.target_solutions(target)
    _dds.SolveBoard(deal._data, target, solutions, 1, fut, 0)
    return SolvedBoard(fut)


def solve_all_boards(
    deals: Iterable[Deal],
    mode: SolveMode = SolveMode.Default,
    target: Optional[int] = None,
) -> SolvedBoardList:
    """
    Optimized version of solve_board for multiple deals which uses threading to
    speed up the calculation

    :param deals: The collection of boards to be solved, each with `first` and `trump` filled
    :param target: If provided, only return cards which can make at least this many tricks
    """
    # Convert deals into boards
    bop = _dds.boards()
    bop.noOfBoards = 0
    target, solutions = mode.target_solutions(target)

    for i, deal in enumerate(deals):
        if i > _dds.MAXNOOFBOARDS:
            raise RuntimeError(f"Too many boards, maximum is {_dds.MAXNOOFBOARDS}")
        bop.deals[i] = deal._data
        bop.target[i] = target
        bop.solutions[i] = solutions
        bop.mode[i] = 1
        bop.noOfBoards += 1

    solvedp = _dds.solvedBoards()
    _dds.SolveAllBoardsBin(bop, solvedp)
    return SolvedBoardList(solvedp)
