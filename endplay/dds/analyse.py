__all__ = [ "analyse_play", "analyse_all_plays" ]

from typing import Iterable, Union, Optional
import endplay._dds as _dds
from endplay.types import Deal, Card, SolvedPlay, SolvedPlayList, Player

def analyse(deal: Deal) -> int:
	"Calculate the most tricks the player on lead can make"
	# Creat empty play trace
	playBin = _dds.playTraceBin()
	playBin.number = 0
	# Calculate and return 13-n, as it returns the tricks from the perspective of RHO
	solvedp = _dds.solvedPlay()
	_dds.AnalysePlayBin(deal._data, playBin, solvedp, 0)
	return 13 - solvedp.tricks[0]

def analyse_play(
	deal: Deal, 
	play: Iterable[Union[Card, str]], 
	perspective: Optional[Player] = None) -> SolvedPlay:
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
	if perspective % 2 != deal.first.rho % 2:
		for i in range(solvedp.number):
			solvedp.tricks[i] = 13 - i
	return SolvedPlay(solvedp)

def analyse_all(deal: Deal) -> int:
	"""
	Optimized version of analyse for multiple deals which uses threading to
	speed up the calculation
	"""
	# Convert deals into boards
	bop = _dds.boards()
	bop.noOfBoards = 0
	for i, deal in enumerate(deals):
		if i > _dds.MAXNOOFBOARDS:
			raise RuntimeError(f"Too many boards, maximum is {_dds.MAXNOOFBOARDS}")
		bop.deals[i] = deal._data
		bop.target[i] = -1
		bop.solutions[i] = 3
		bop.mode[i] = 0
		bop.noOfBoards += 1
	# Create empty play traces
	plp = _dds.playTracesBin()
	plp.noOfBoards = bop.noOfBoards
	for i in range(plp.noOfBoards):
		plp[i].number = 0

	# Calculate and return 13-n, as it returns the tricks from the perspective of RHO
	solvedp = _dds.solvedPlays()
	_dds.AnalyseAllPlaysBin(bop, plp, solvedp, 0)
	return [13 - solvedp.solved[i].tricks[i] for i in range(plp.noOfBoards)]

def analyse_all_plays(
	deals: Iterable[Deal], 
	plays: Iterable[Iterable[Card]], 
	perspective: Optional[Player] = None) -> SolvedPlayList:
	"""
	Optimized version of analyse_play for multiple deals which uses
	threading to speed up the calculation
	"""
	# Convert deals into boards
	bop = _dds.boards()
	bop.noOfBoards = 0
	for i, deal in enumerate(deals):
		if i > _dds.MAXNOOFBOARDS:
			raise RuntimeError(f"Too many boards, maximum is {_dds.MAXNOOFBOARDS}")
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
	for i in range(bop.noOfBoards):
		if perspective % 2 != (bop.deals[i].first + 1) % 2:
			for j in range(solvedp.solved[i].number):
				solvedp.solved[i].tricks[j] = 13 - solvedp.solved[i].tricks[j]
	return SolvedPlayList(solvedp)