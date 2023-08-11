from __future__ import annotations

__all__ = ["Hand"]

import ctypes
import sys
from collections.abc import Iterable, Iterator
from typing import Union

import endplay._dds as _dds
from endplay.config import suppress_unicode
from endplay.types.card import Card
from endplay.types.denom import Denom
from endplay.types.rank import Rank
from endplay.types.suitholding import SuitHolding


class Hand:
    "Class allowing manipulations of cards in the hand of a single player"

    def __init__(self, data: Union[str, ctypes.Array[ctypes.c_uint]] = "..."):
        """
        Construct a hand object

        :param data: Either a PBN string of the hand, or a reference to a _dds object
        """
        if isinstance(data, str):
            self._data = (ctypes.c_uint * 4)(0, 0, 0, 0)
            suits = data.split(".")
            if len(suits) > 4:
                raise RuntimeError(f"hand contains more than four suits: {data})")
            for i, suit in enumerate(suits):
                if suit and suit[0].upper() in "SHDC":
                    suit = suit[1:]
                for rank in suit:
                    self._data[i] |= Rank.find(rank).value
        else:
            self._data = data

    def __copy__(self) -> "Hand":
        return Hand((ctypes.c_uint * 4).from_buffer_copy(self._data))

    def copy(self) -> "Hand":
        return self.__copy__()

    def add(self, card: Union[Card, str]) -> bool:
        """
        Adds a card to the hand

        :param card: The card to be added to the hand
        :return: False if the card was already in the hand, True otherwise
        """
        if isinstance(card, str):
            card = Card(name=card)

        if card in self:
            return False
        self._data[card.suit.value] |= card.rank.value
        return True

    def extend(self, cards: Iterable[Union[Card, str]]) -> int:
        """
        Add multiple cards to the hand

        :param cards: An iterable of the cards to add
        :return: The number of cards successfully added
        """
        return sum(self.add(card) for card in cards)

    def remove(self, card: Union[Card, str]) -> bool:
        """
        Remove a card from the hand

        :param card: The card to be added to the hand, can be a string
                representation e.g. "CQ"
        :return: False if the card wasn't in the hand, True otherwise
        """
        if isinstance(card, str):
            card = Card(name=card)

        if card in self:
            self._data[card.suit.value] &= ~card.rank.value
            return True
        return False

    @staticmethod
    def from_pbn(pbn: str) -> "Hand":
        """
        Construct a Hand from a PBN string

        :param pbn: A PBN string for a hand, e.g. "QT62..AQT852.QJT"
        """
        return Hand(pbn)

    def to_pbn(self) -> str:
        ":return: A PBN representation of the hand"
        return ".".join(str(self[suit]) for suit in Denom.suits())

    @staticmethod
    def from_lin(lin: str) -> "Hand":
        """
        Construct a Hand from a LIN string

        :param lin: A LIN string for a hand, e.g. "SQT62HDAQT852CQJT"
        """
        pbn = lin[1:].replace("H", ".").replace("D", ".").replace("C", ".")
        return Hand.from_pbn(pbn)

    def to_lin(self) -> str:
        """
        Convert a Hand to a LIN string
        """
        lin = ""
        with suppress_unicode():
            for suit in Denom.suits():
                lin += suit.abbr + self[suit].to_pbn()[::-1]
        return lin

    def to_LaTeX(self, vertical: bool = True, ten_as_letter: bool = False) -> str:
        """
        Create a LaTeX representation of the hand.

        :param vertical: If True uses \\vhand, else \\hhand layout
        :param ten_as_letter: Prints a T for tens if True, else prints 10
        """
        if vertical:
            res, sep = r"\begin{tabular}{l}", r"\\"
        else:
            res, sep = "", " "
        for suit in Denom.suits():
            res += "$\\" + suit.name + "uit$ "
            if len(self[suit]) == 0:
                res += "---"
            else:
                for rank in self[suit]:
                    res += r"\makebox[.8em]{"
                    res += (
                        r"1\kern-.16em0"
                        if (rank == Rank.RT and not ten_as_letter)
                        else rank.abbr
                    )
                    res += "}"
            res += sep
        if vertical:
            res += r"\end{tabular}"
        return res

    def pprint(self, vertical: bool = True, stream=sys.stdout) -> None:
        "Print the suits in the hand using suit symbols"
        sep = "\n" if vertical else " "
        print(
            sep.join(f"{suit.abbr} {self[suit]}" for suit in Denom.suits()), file=stream
        )

    def clear(self) -> None:
        "Remove all cards from the hand"
        for denom in Denom.suits():
            self[denom].clear()

    @property
    def spades(self) -> SuitHolding:
        "The spade holding of the hand"
        return self[Denom.spades]

    @spades.setter
    def spades(self, suit: Union[SuitHolding, str]) -> None:
        self[Denom.spades] = suit

    @property
    def hearts(self) -> SuitHolding:
        "The heart holding of the hand"
        return self[Denom.hearts]

    @hearts.setter
    def hearts(self, suit: Union[SuitHolding, str]) -> None:
        self[Denom.hearts] = suit

    @property
    def diamonds(self) -> SuitHolding:
        "The diamond holding of the hand"
        return self[Denom.diamonds]

    @diamonds.setter
    def diamonds(self, suit: Union[SuitHolding, str]) -> None:
        self[Denom.diamonds] = suit

    @property
    def clubs(self) -> SuitHolding:
        "The club holding of the hand"
        return self[Denom.clubs]

    @clubs.setter
    def clubs(self, suit: Union[SuitHolding, str]) -> None:
        self[Denom.clubs] = suit

    def __contains__(self, card: Union[Card, str]) -> bool:
        ":return: True if card is in this hand"
        if isinstance(card, str):
            card = Card(name=card)

        return bool(self._data[card.suit.value] & card.rank.value)

    def __str__(self) -> str:
        ":return: A PBN string representation of the hand"
        return self.to_pbn()

    def __repr__(self) -> str:
        return f'Hand("{self.to_pbn()}")'

    def __iter__(self) -> Iterator[Card]:
        ":return: An iterator over the suit holdings in the order spades, hearts, diamonds and clubs"
        for suit in Denom.suits():
            for rank in self[suit]:
                yield Card(suit=suit, rank=rank)

    def __getitem__(self, suit: Denom) -> SuitHolding:
        ":return: The specified suit holding of the hand"
        return SuitHolding(self._data, suit.value)

    def __setitem__(self, suit: Denom, holding: Union[SuitHolding, str]) -> None:
        if isinstance(holding, str):
            self[suit].clear()
            for rank in holding:
                self[suit].add(rank)
        else:
            self._data[suit] = holding._data[holding._idx]

    def __len__(self) -> int:
        ":return: The number of cards in the hand"
        return sum(bin(suit).count("1") for suit in self._data)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hand):
            return NotImplemented
        return not _dds._libc.memcmp(self._data, other._data, len(self._data))
