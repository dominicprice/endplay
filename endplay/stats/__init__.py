__all__ = ["average", "average_tricks"]

from endplay.types import Deal, Denom, Player, SuitHolding
from endplay.dds.analyse import analyse_all_plays
from typing import Iterable, Callable, Optional
from itertools import combinations
import numpy as np

def average(deals: Iterable[Deal], func: Callable[[Deal], float]):
	"Calculate the average of a function over multiple deals"
	acc, n = .0, 0
	for deal in deals:
		acc += func(deal)
		n += 1
	return acc / n

def average_tricks(deals: Iterable[Deal]):
	"""
	Calculate the average number of tricks each deal will produce. The number
	of tricks is shown from the perspective of the player to the left of
	deal.first (as this is assumed to be declarer)
	"""
	def empty_plays():
		for _ in range(len(deals)): yield []
	try:
		l = len(deals)
	except TypeError:
		deals = list(deals)
		l = len(deals)
	res = analyse_all_plays(deals, [[]] * l)
	tot = 0.0
	for x in res:
		tot += x[0]
	return tot / len(res)

def all_combinations(suit: SuitHolding):
	for r in range(len(suit) + 1):
		for comb in combinations(suit, r):
			east, west = SuitHolding(), SuitHolding()
			for rank in suit:
				if rank in comb:
					east.add(rank)
				else:
					west.add(rank)
			yield east, west

def analyse_suit_play(north: SuitHolding, south: SuitHolding, missing: Optional[SuitHolding] = None, *conditions: Iterable[Callable[[SuitHolding], bool]]):
	"""
	Analyse all possible ways of playing a suit holding, and calculate the average number of tricks
	that each play will yield
	"""
	raise NotImplementedError

	# Deal all remaining cards to the missing pile
	if missing is None:
		missing = SuitHolding("AKQJT98765432")
		for rank in north: missing.remove(rank)
		for rank in south: missing.remove(rank)
	# Calculate all possible ways of playing the suit

	# Set up the deal object, and the list of cards we give to other players
	deal = Deal()
	deal.trump = notrumps
	for east, west in all_combinations(missing):
		# Deal cards to all players
		deal.north.spades = north
		deal.south.spades = south
		deal.east.spades = east
		deal.west.spades = west
		# Find the player with the longest hand
		longest = max(len(hand) for hand in deal)
		# Pad out the other player's hands with cards. Just give them
		# each a separate suit so the solver doesn't have to spend any
		# time analysing those paths
		denom = 1
		for player in Player:
			plen = longest - len(deal[player])
			if plen == 0:
				continue
			for i in range(plen):
				deal[player][denom].add(i)
			denom += 1
		
