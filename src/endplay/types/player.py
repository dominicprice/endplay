from __future__ import annotations

__all__ = ["Player"]

from enum import IntEnum
from collections.abc import Iterator, Iterable

class Player(IntEnum):
	"Encoding for player seat"
	north	= 0
	east	= 1
	south	= 2
	west	= 3
	
	@staticmethod
	def find(name: str) -> 'Player':
		"Convert a string into a Player object"
		return Player("NESW".index(name[0].upper()))
	
	@staticmethod
	def from_lin(n: int) -> 'Player':
		"""
		Convert a BBO LIN representation of a player into a Player object.
		The conversion is determined by 1=S, 2=W, 3=N, 4=E
		"""
		return [Player.south, Player.west, Player.north, Player.east][n - 1]

	def to_lin(self) -> int:
		return [3,4,1,2][self]

	@staticmethod
	def from_board(n: int) -> 'Player':
		"""
		Return the player who is the dealer of the corresponding board
		"""
		return Player.west.next(n)

	def enumerate(self, iterable: Iterable, step: int = 1) -> Iterator:
		"""
		Return an iterator whose `next` method returns a tuple
		containing a Player (starting from this player) and the
		values obtained from iterating over iterable, where the
		player increments each time by `step` rotations clockwise
		"""
		player = self
		for item in iterable:
			yield player, item
			player = player.next(step)

	def iter_from(self) -> Iterator['Player']:
		"""
		Iterate over all four players, clockwise, starting from
		this player

		:return: An iterator over all four players in play order
		"""
		for i in range(4):
			yield self.next(i)
		
	@staticmethod
	def iter_order(order: str) -> Iterator['Player']:
		"""
		Iterate over a sequence of players in a given order

		:param order: The specified order as a four-character string or list of strings
		:return: An iterator over the players in the specified order
		"""
		yield from (Player.find(c) for c in order)

	def turns_to(self, other: 'Player') -> int:
		"Return the number of positions clockwise `other` is from `self`"
		distance = int(other) - int(self)
		if distance < 0:
			distance += 4
		return distance
		
	def prev(self, n: int = 1) -> 'Player':
		":return: The player who is n places right of the current player"
		return Player((self-n)  % 4)
		
	def next(self, n: int = 1) -> 'Player':
		":return: The player who is n places left of the current player"
		return Player((self + n) % 4)

	@property
	def lho(self) -> 'Player':
		":return: The player on the current player's left"
		return self.next(1)
	@property
	def partner(self) -> 'Player':
		":return: The player opposite the current player"
		return Player((self + 2) % 4)
	@property
	def rho(self) -> 'Player':
		":return: The player to the current player's right"
		return self.prev(1)
		
	@property
	def abbr(self) -> str:
		":return: A single character string for the player name"
		return self.name[0].upper()
