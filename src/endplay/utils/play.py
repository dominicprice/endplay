"""
Miscellaneous functions relating to play history
"""

from __future__ import annotations

__all__ = [
	"trick_winner", "total_tricks", "tricks_to_result", 
	"result_to_tricks", "linearise_play"]

from endplay.types import Card, Player, Denom, Rank
from collections.abc import Iterable
from itertools import zip_longest

# copied from more_itertools for backwards compatibility with old versions of the
# library which swapped the order of the first two parameters
def _grouper(iterable, n, fillvalue=None):
	args = [iter(iterable)] * n
	return zip_longest(fillvalue=fillvalue, *args)

def trick_winner(trick: Iterable[Card], first: Player, trump: Denom):
	"Calculate the winner of a trick"
	winner, topcard = first, trick[0]
	for i in range(1, 4):
		if trick[i].suit == topcard.suit:
			if trick[i].rank > topcard.rank:
				winner, topcard = first.next(i), trick[i]
		elif trick[i].suit == trump:
			winner, topcard = first.next(i), trick[i]
	return winner

def total_tricks(play: Iterable[Card], trump: Denom):
	"""
	Calculate the total number of tricks made by the side
	initially on lead in `play` with the given trump suit
	"""
	first = Player.north
	tricks = 0
	for trick in _grouper(play, 4):
		winner = trick_winner(trick, first, trump)
		if winner in [Player.north, Player.south]:
			tricks += 1
	return tricks

def tricks_to_result(tricks: int, level: int):
	"""
	Convert tricks made to a result, e.g. 8 tricks
	in a 4-level contract becomes -2
	"""
	return tricks - (level + 6)

def result_to_tricks(result: int, level: int):
	"""
	Convert a result to tricks made, e.g. +1 in a
	3 level contract becomes 10
	"""
	return 6 + level + result

def linearise_play(
		table: list[Card], 
		first: Player, 
		trump: Denom,
		pad_value: Card = Card(suit=Denom.nt, rank=Rank.R2))-> list[str]:
	"""
	Convert a table-style play history to a linear play history.
	PBN record play history is in blocks of four tricks always
	starting with the same player, but many double dummy solving
	algorithms rely on a linear play history where cards are recorded
	in the order they are played. 

	Some data formats include the ability to write cards with an unimportant
	value, and which are required for the table structure. The `pad_value` 
	parameter should be set to a sentinel value (usually a card with nt suit)
	to be recognised
	"""
	play = []
	winner = first
	for row in table:
		# rotate the trick so that the winner is first
		rots = first.turns_to(winner)
		trick = row[rots:] + row[:rots]
		play += trick
		winner = trick_winner(trick, winner, trump)
	# The last trick may have dummy cards (signified by denom=Denom.nt) to
	# fill out the whole trick if there was a claim; if so remove those now
	while play and play[-1] == pad_value:
		play = play[:-1]
	return play

def tabularise_play(
	play: list[Card], 
	first: Player, 
	trump: Denom,
	*,
	pad_value: Card = Card(suit=Denom.nt, rank=Rank.R2)):
	"""
	Convert a linear play sequence into a table, where the first element in each row
	is the card played by the player `first`. 
	If the number of tricks in the play sequence is not not divisible by four, then the
	table will be padded out with `pad_value`.
	"""
	table = []
	winner = first
	for trick in _grouper(play, 4, pad_value):
		new_winner = trick_winner(trick, winner, trump)
		# rotate the trick so that first is first
		rots = winner.turns_to(first)
		trick = trick[rots:] + trick[:rots]
		table.append(trick)
		winner = new_winner
	return table
	


