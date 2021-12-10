from __future__ import annotations	

__all__ = ["Denom"]

from enum import IntEnum
from collections.abc import Iterator

class Denom(IntEnum):
	"Encoding for suits and contract denomination"
	spades		= 0
	hearts		= 1
	diamonds	= 2
	clubs		= 3
	nt			= 4

	@staticmethod
	def find(name: str) -> 'Denom':
		"Convert a string value into a Denom object"
		try:
			return Denom("SHDCN♠♥♦♣N♤♡♢♧".index(name[0].upper()) % 5)
		except ValueError:
			raise ValueError(f"Could not convert {name} into a Denom object")

	@staticmethod
	def bidorder() -> Iterator['Denom']:
		":return: An iterator over all the denominations in the order they appera in a bidding box"
		yield from [Denom.clubs, Denom.diamonds, Denom.hearts, Denom.spades, Denom.nt]

	@staticmethod 
	def suits(reverse: bool = False) -> Iterator['Denom']:
		"""
		Iterate over the suits, excluding notrumps

		:param reverse: If true, return suits in the order clubs -> spades
		:return: An iterator over the four suits
		"""
		r = range(3,-1,-1) if reverse else range(4)
		for i in r:
			yield Denom(i)

	def is_suit(self) -> bool:
		":return: True if the denomination is not notrumps"
		return self in Denom.suits()

	def is_major(self) -> bool:
		":return: True if the denomination is spades or hearts"
		return self in [ Denom.spades, Denom.hearts ]

	def is_minor(self) -> bool:
		":return: True if the denomination is diamonds or clubs"
		return self in [ Denom.diamonds, Denom.clubs ]

	@property
	def abbr(self) -> str:
		":return: A short identifier for the denomination"
		import endplay.config as config
		if self == Denom.nt:
			return "NT"
		elif config.use_unicode:
			return "♠♥♦♣"[self]
		else:
			return "SHDC"[self]
