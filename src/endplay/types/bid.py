from __future__ import annotations

__all__ = [ "Bid", "ContractBid", "PenaltyBid" ]

import sys
from more_itertools import chunked
from endplay.types.denom import Denom
from endplay.types.penalty import Penalty
from endplay.types.player import Player
from collections.abc import Iterable
from typing import Optional, Union, NoReturn, TextIO

class Bid:
	"""
	Base class representing an auction call. This class provides a convenience
	constructor from a string, but upon construction will automatically donwcast
	its type to one of :class:`ContractBid` or :class:`PenaltyBid` depending on the type of the
	call.

	:ivar alertable: Flag indicating whether the bid is alertable
	:vartype alertable: bool
	:ivar announcement: String transcription of the announcement for this bid
	:vartype announcement: Optional[str]
	"""
	def __init__(self, name: str, alertable: bool = False, announcement: Optional[str] = None):
		try:
			penalty = Penalty.find(name)
			object.__setattr__(self, "__class__", PenaltyBid)
			PenaltyBid.__init__(self, penalty, alertable, announcement)
		except ValueError:
			level, denom = int(name[0]), Denom.find(name[1])
			object.__setattr__(self, "__class__", ContractBid)
			ContractBid.__init__(self, level, denom, alertable, announcement)

	def __setattr__(self, attr: str, value: str) -> Union[None, NoReturn]:
		if attr in ["alertable", "announcement"]:
			object.__setattr__(self, attr, value)
		else:
			raise TypeError("Cannot assign to immutable Bid object")

	def __delattr__(self, attr: str) -> NoReturn:
		raise TypeError("Cannot delete attribute of immutable Bid object")
		
class ContractBid(Bid):
	"""
	Class representing a call that names a contract, i.e. has a level and strain

	:ivar level: The level of the call (between 1 and 7)
	:vartype level: int
	:ivar denom: The strain of the call
	:vartype strain: Denom
	:ivar alertable: Flag indicating whether the bid is alertable
	:vartype alertable: bool
	:ivar announcement: String transcription of the announcement for this bid
	:vartype announcement: Optional[str]
	"""
	def __init__(self, 
		level: int, 
		denom: Denom, 
		alertable: bool = False, 
		announcement: Optional[str] = None):
		object.__setattr__(self, "level", level)
		object.__setattr__(self, "denom", denom)
		object.__setattr__(self, "alertable", alertable)
		object.__setattr__(self, "announcement", announcement)

	def __repr__(self):
		return f"ContractBid(denom={self.denom!r}, level={self.level!r}, alertable={self.alertable!r}, announcement={self.announcement!r})"

	def __str__(self):
		return f"{self.level}{self.denom.abbr}" + ("!" if self.alertable else "") + ("*" if self.announcement else "")

class PenaltyBid(Bid):
	"""
	Class representing a call that does not name a contract, i.e. pass, double or redouble
	
	:ivar penalty: The type of the call
	:vartype penalty: Penalty
	:ivar alertable: Flag indicating whether the bid is alertable
	:vartype alertable: bool
	:ivar announcement: String transcription of the announcement for this bid
	:vartype announcement: Optional[str]
	"""
	def __init__(self, 
		penalty: Penalty, 
		alertable: bool = False,
		announcement: Optional[str] = None):
		object.__setattr__(self, "penalty", penalty)
		object.__setattr__(self, "alertable", alertable)
		object.__setattr__(self, "announcement", announcement)

	def __repr__(self):
		return f"PenaltyBid(penalty={self.penalty!r}, alertable={self.alertable!r}, announcement={self.announcement!r})"

	def __str__(self):
		return (self.penalty.abbr or "p").upper() + ("!" if self.alertable else "") + ("*" if self.announcement else "")
