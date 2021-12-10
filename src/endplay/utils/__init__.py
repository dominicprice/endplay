"""
Miscellaneous functions
"""

from __future__ import annotations

__all__ = [
	"trick_winner", "total_tricks", "tricks_to_result", "result_to_tricks",
	"linearise_play", "escape_suits", "unescape_suits"]

import re
from endplay.types import Card, Player, Denom
from collections.abc import Iterable

def grouper(iterable, n):
	"""
	Iterate over `iterable` groups of length `n`. If `len(iterable) % n != 0`,
	then the last group will contains less than `n` elements
	"""
	def take_n(iterator, n):
		try:
			for _ in range(n):
				yield next(iterator)
		except StopIteration:
			pass
	iterator = iter(iterable)
	res = tuple(take_n(iterator, n))
	while len(res) != 0:
		yield res
		res = tuple(take_n(iterator, n))
		
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
	for trick in grouper(play, 4):
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

def linearise_play(table: list[Card], first: Player) -> list[str]:
	"""
	Convert a table-style play history to a linear play history.
	PBN record play history is in blocks of four tricks always
	starting with the same player, but many double dummy solving
	algorithms rely on a linear play history where cards are recorded
	in the order they are played. 
	"""
	play = []
	winner = first
	for trick in grouper(play, 4):
		# rotate the trick so that the winner is first
		rots = first.turns_to(winner)
		trick = trick[rots:] + trick[:rots]
		play += trick
		winner = trick_winner(trick)
	# The last trick may have dummy cards (signified by denom=Denom.nt) to
	# fill out the whole trick if there was a claim; if so remove those now
	while play and play[-1].denom == Denom.nt:
		play = play[:-1]

_escape_suits_table = str.maketrans({
	"♠": "!S",
	"♥": "!H",
	"♦": "!D",
	"♣": "!C"
})

def escape_suits(s: str):
	"""
	Escape unicode suit symbols into BBO suit notation (!S, !H, !D, !C)
	"""
	return s.translate(_escape_suits_table)

def unescape_suits(s: str):
	"""
	Unescape BBO suit notation (!S, !H, !D, !C) into unicode suit symbols
	"""
	s = re.sub("!s", "♠", s, flags=re.IGNORECASE)
	s = re.sub("!h", "♥", s, flags=re.IGNORECASE)
	s = re.sub("!d", "♦", s, flags=re.IGNORECASE)
	return re.sub("!c", "♣", s, flags=re.IGNORECASE)