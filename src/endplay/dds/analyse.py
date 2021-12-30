"""
Analysis functions from the DDS library, which calculate the double dummy
number of tricks available given a play history.
"""

from __future__ import annotations

__all__ = [ 
	"SolvedPlay", "SolvedPlayList", "analyse_start", "analyse_play", 
	"analyse_all_plays", "analyse_all_starts" ]

from typing import Union
from collections.abc import Iterable, Sequence
from endplay.types import Deal, Card
import endplay._dds as _dds

class SolvedPlay(Sequence):
	def __init__(self, data: _dds.solvedPlay):
		self._data = data

	def __len__(self) -> int:
		":return: The number of results in the play"
		return self._data.number

	def __getitem__(self, i: int) -> int:
		":return: The number of tricks that declarer can make after the ith card is played"
		if i < 0:
			i = len(self) - i
		if i < 0 or i >= len(self):
			raise IndexError
		return self._data.tricks[i]

	def __repr__(self) -> str:
		return f'<SolvedPlay object; data={self!s}>'

	def __str__(self) -> str:
		return "(" + ", ".join(str(p) for p in self) + ")"

class SolvedPlayList(Sequence):
	def __init__(self, data: _dds.solvedPlays):
		self._data = data

	def __len__(self) -> int:
		":return: The number of boards in the list"
		return self._data.noOfBoards

	def __getitem__(self, i: int) -> SolvedPlay:
		":return: The solved play at index `i`"
		if i < 0:
			i = len(self) - i
		if i < 0 or i >= len(self):
			raise IndexError
		return SolvedPlay(self._data.solved[i])

	def __repr__(self) -> str:
		return f'<SolvedPlayList; length={len(self)}'

	def __str__(self) -> str:
		return "[" + ", ".join(str(s) for s in self) + "]"

def analyse_start(deal: Deal, declarer_is_first: bool = False) -> int:
	"""
	Calculate the most tricks declarer can make.

	:param deal: The deal to analyse
	:param declarer_is_first: The algorithm assumes that the person who leads is to the left
		of the declarer (as would be the case with the first card led
		to a hand), but to return the result as seen from the leader's
		perspective you can set this to True
	"""
	# Create empty play trace
	playBin = _dds.playTraceBin()
	playBin.number = 0
	# Calculate and return 13-n, as it returns the tricks from the perspective of RHO
	solvedp = _dds.solvedPlay()
	_dds.AnalysePlayBin(deal._data, playBin, solvedp, 0)
	if declarer_is_first:
		return len(deal[deal.first]) - solvedp.tricks[0]
	else:
		return solvedp.tricks[0]

def analyse_play(
	deal: Deal, 
	play: Iterable[Union[Card, str]], 
	declarer_is_first: bool = False) -> SolvedPlay:
	"""
	Calculate a list of double dummy values after each card in `play`
	is played to the hand. This returns `len(play)+1` results, as there
	is also a result before any card has been played
	"""
	# Convert play to playTraceBin
	playBin = _dds.playTraceBin()
	playBin.number = 0
	for i, card in enumerate(play):
		if isinstance(card, str):
			card = Card(card)
		playBin.suit[i] = card.suit
		playBin.rank[i] = card.rank.to_alternate()
		playBin.number += 1

	# Solve and correct trick count if perspective is wrong way round
	solvedp = _dds.solvedPlay()
	_dds.AnalysePlayBin(deal._data, playBin, solvedp, 0)
	if declarer_is_first:
		starting_cards = len(deal[deal.first])
		for i in range(solvedp.number):
			solvedp.tricks[i] = starting_cards - solvedp.tricks[i]
	return SolvedPlay(solvedp)

def analyse_all_starts(
	deals: Iterable[Deal], 
	declarer_is_first: bool = False) -> list[int]:
	"""
	Optimized version of analyse for multiple deals which uses threading to
	speed up the calculation
	"""
	# Convert deals into boards
	bop = _dds.boards()
	bop.noOfBoards = 0
	if declarer_is_first:
		# We need to keep track of how many cards the person on lead starts
		# with, so that we can invert the result
		starting_cards = []
	for i, deal in enumerate(deals):
		if i > _dds.MAXNOOFBOARDS:
			raise RuntimeError(f"Too many boards, maximum is {_dds.MAXNOOFBOARDS}")
		if declarer_is_first:
			starting_cards.append(len(deal[deal.first]))
		bop.deals[i] = deal._data
		bop.target[i] = -1
		bop.solutions[i] = 3
		bop.mode[i] = 0
		bop.noOfBoards += 1
	# Create empty play traces
	plp = _dds.playTracesBin()
	plp.noOfBoards = bop.noOfBoards
	for i in range(plp.noOfBoards):
		plp.plays[i].number = 0

	# Calculate and return 13-n, as it returns the tricks from the perspective of RHO
	solvedp = _dds.solvedPlays()
	_dds.AnalyseAllPlaysBin(bop, plp, solvedp, 0)
	if declarer_is_first:
		return [starting_cards[i] - solvedp.solved[i].tricks[0] for i in range(plp.noOfBoards)]
	else:
		return [solvedp.solved[i].tricks[0] for i in range(plp.noOfBoards)]

def analyse_all_plays(
	deals: Iterable[Deal], 
	plays: Iterable[Iterable[Card]], 
	declarer_is_first: bool = False) -> SolvedPlayList:
	"""
	Optimized version of analyse_play for multiple deals which uses
	threading to speed up the calculation
	"""
	# Convert deals into boards
	bop = _dds.boards()
	bop.noOfBoards = 0
	if declarer_is_first:
		starting_cards = []
	for i, deal in enumerate(deals):
		if i > _dds.MAXNOOFBOARDS:
			raise RuntimeError(f"Too many boards, maximum is {_dds.MAXNOOFBOARDS}")
		if declarer_is_first:
			starting_cards.append(len(deal[deal.first]))
		bop.deals[i] = deal._data
		bop.target[i] = -1
		bop.solutions[i] = 3
		bop.mode[i] = 0
		bop.noOfBoards += 1

	# Convert plays into playTracesBin
	plp = _dds.playTracesBin()
	plp.noOfBoards = 0
	for i, play in enumerate(plays):
		plp.plays[i].number = 0
		for j, card in enumerate(play):
			if isinstance(card, str):
				card = Card(card)
			plp.plays[i].suit[j] = card.suit
			plp.plays[i].rank[j] = card.rank.to_alternate()
			plp.plays[i].number += 1
		plp.noOfBoards += 1

	solvedp = _dds.solvedPlays()
	_dds.AnalyseAllPlaysBin(bop, plp, solvedp, 0)
	if declarer_is_first:
		for i in range(bop.noOfBoards):
			for j in range(solvedp.solved[i].number):
				solvedp.solved[i].tricks[j] = starting_cards[i] - solvedp.solved[i].tricks[j]
	return SolvedPlayList(solvedp)