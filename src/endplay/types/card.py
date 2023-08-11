__all__ = ["Card"]

from dataclasses import dataclass
from typing import Optional

from endplay.types.denom import Denom
from endplay.types.rank import Rank


@dataclass(frozen=True)
class Card:
    """
    Immutabale class representing a card with `suit` and `rank` read-only attributes

    :ivar suit: The suit of the card
    :vartype suit: Denom
    :ivar rank: The rank of the card
    :vartype rank: Rank
    """

    rank: Rank
    suit: Denom

    def __init__(
        self,
        name: Optional[str] = None,
        *,
        suit: Optional[Denom] = None,
        rank: Optional[Rank] = None,
    ):
        """
        Construct a card either from a string name or from Denom and Rank objects

        :param name: The name of the card, e.g. "S9" or "HT"
        :param suit: The suit of the card
        :param rank: The rank of the card
        """
        if name is None:
            if suit is None or rank is None:
                raise ValueError("either name or both suit and rank must be defined")
            object.__setattr__(self, "suit", suit)
            object.__setattr__(self, "rank", rank)
        else:
            suit = Denom.find(name[0])
            rank = Rank.find(name[1])

        if not isinstance(suit, Denom):
            raise ValueError("suit must be of type Denom")
        object.__setattr__(self, "suit", suit)

        if not isinstance(rank, Rank):
            raise ValueError("rank must be of type Rank")
        object.__setattr__(self, "rank", rank)

    def __str__(self) -> str:
        return f"{self.suit.abbr}{self.rank.abbr}"
