__all__ = ["Card"]

from endplay.types.denom import Denom
from endplay.types.rank import Rank

class Card:
	"Representation of a card as a suit and rank"
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
				self.suit = Denom("SHDC".index(suit))
				self.rank = Rank[f"R{rank}"]
			except ValueError:
				raise ValueError(f"Could not parse card name {name}: invalid suit")
			except KeyError:
				raise ValueError(f"Could not parse card name {name}: invalid rank")
		else:
			if not isinstance(suit, Denom):
				raise ValueError("suit must be of type Denom")
			self.suit = suit
			if not isinstance(rank, Rank):
				raise ValueError("rank must be of type Rank")
			self.rank = rank
			
	def __hash__(self):
		return hash((self.rank, self.suit))

	def __eq__(self, other: 'Card') -> bool:
		return self.rank == other.rank and self.suit == other.suit

	def __repr__(self) -> str:
		return f"Card('{self!s}')"
		
	def __str__(self) -> str:
		return f"{self.suit.abbr}{self.rank.abbr}"
