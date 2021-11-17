__all__ = ["Player"]

from enum import IntEnum
from typing import Iterator

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
	def iter_from(player: 'Player') -> Iterator['Player']:
		"""
		:param player: The first player in the returned iterator
		:return: An iterator over all four players in play order
		"""
		yield from (Player(i % 4) for i in range(player, player + 4))
		
	@staticmethod
	def iterorder(order: str) -> Iterator['Player']:
		"""
		:order: The specified order as a four-character string or list of strings
		:return: An iterator over the players in the specified order
		"""
		yield from (Player.find(c) for c in order)
		
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
