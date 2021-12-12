__all__ = ["Card"]

from endplay.types.denom import Denom
from endplay.types.rank import Rank
from typing import NoReturn, Any

class Card:
	"""
	Immutabale class representing a card with `suit` and `rank` read-only attributes
	
	:ivar suit: The suit of the card
	:vartype suit: Denom
	:ivar rank: The rank of the card
	:vartype rank: Rank
	"""
	def __init__(self, name: str = None, *, suit: Denom = None, rank: Rank = None):
		"""
		Construct a card either from a string name or from Denom and Rank objects

		:param name: The name of the card, e.g. "S9" or "HT"
		:param suit: The suit of the card
		:param rank: The rank of the card
		"""
		if name is not None:
			try:
				suit, rank = name.upper()
			except ValueError:
				raise ValueError(f"Could not parse card name {name}: must be 2 characters in length")
			try:	
				suit = Denom("SHDC".index(suit))
				rank = Rank[f"R{rank}"]
			except ValueError:
				raise ValueError(f"Could not parse card name {name}: invalid suit")
			except KeyError:
				raise ValueError(f"Could not parse card name {name}: invalid rank")
		if not isinstance(suit, Denom):
			raise ValueError("suit must be of type Denom")
		if not isinstance(rank, Rank):
			raise ValueError("rank must be of type Rank")

		object.__setattr__(self, "suit", suit)
		object.__setattr__(self, "rank", rank)
			
	def __setattr__(self, attr: str, value: Any) -> NoReturn:
		raise TypeError("Cannot assign to immutable Card object")

	def __delattr__(self, attr: str) -> NoReturn:
		raise TypeError("Cannot delete attribute of immutable Card object")

	def __hash__(self):
		return hash((self.rank, self.suit))

	def __eq__(self, other: 'Card') -> bool:
		return self.rank == other.rank and self.suit == other.suit

	def __repr__(self) -> str:
		return f"Card('{self!s}')"
		
	def __str__(self) -> str:
		return f"{self.suit.abbr}{self.rank.abbr}"
