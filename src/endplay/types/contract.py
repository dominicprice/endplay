__all__ = ["Contract"]

from typing import Iterable, Union
from endplay.types.player import Player
from endplay.types.denom import Denom
from endplay.types.penalty import Penalty
from endplay.types.vul import Vul
import endplay._dds as _dds
import re

contract_to_denom = [ Denom.nt, Denom.spades, Denom.hearts, Denom.diamonds, Denom.clubs ]
denom_to_contract = [ 1, 2,3,4,0 ]

class Contract:
	"Class representing a specific contract"
	_pat = re.compile(r"^([1-7])((?:NT)|S|H|D|C)([NSEW])(X{0,2})(=|(?:[+-]\d+))$")
	def __init__(
		self, 
		data: Union[_dds.contractType, str, None] = None, 
		*, 
		level: int = None, 
		denom: Denom = None, 
		declarer: Player = None, 
		penalty: Penalty = None, 
		result: int = None):
		"""
		Construct a new contract
		:param data: Construct from a _dds.contractType object or contract string
		:param level: The level of the contract
		:param denom: The denomination of the contract
		:param declarer: The declarer of the contract
		:param result: The number of overtricks (positive) or undertricks (negative) made
		:param penalty: The penalty (pass, x or xx) of the contract
		"""
		if isinstance(data, str):
			m = Contract._pat.match(data.upper())
			if not m:
				raise ValueError(f"Invalid contract string: {data}")
			level = int(m[1])
			denom = Denom.find(m[2])
			declarer = Player.find(m[3])
			penalty = Penalty.find(m[4])
			result = 0 if m[5] == "=" else int(m[5])
			data = None

		self._data = data or _dds.contractType()
		self.penalty = Penalty.none if self._data.underTricks == 0 else Penalty.doubled
		if level is not None: self.level = level
		if denom is not None: self.denom = denom
		if declarer is not None: self.declarer = declarer
		if penalty is not None: self.penalty = penalty
		if result is not None: self.result = result

	@property
	def level(self) -> int:
		return self._data.level
	@level.setter
	def level(self, new_level: int) -> None:
		self._data.level = new_level

	@property
	def denom(self) -> Denom:
		"The denomination of the contract"
		return contract_to_denom[self._data.denom]
	@denom.setter
	def denom(self, new_denom: Denom) -> None:
		self._data.denom = denom_to_contract[new_denom]

	@property
	def declarer(self) -> Player:
		"The declarer of the contract"
		return Player(self._data.seats)
	@declarer.setter
	def declarer(self, player: Player):
		self._data.seats = player

	@property
	def result(self) -> int:
		"The number of tricks over or under the contract made"
		if self._data.underTricks != 0:
			return -self._data.underTricks
		if self._data.overTricks != 0:
			return self._data.overTricks
		return 0
	@result.setter
	def result(self, tricks: int):
		if tricks > 0:
			self._data.underTricks = 0
			self._data.overTricks = tricks
		else:
			self._data.underTricks = -tricks
			self._data.overTricks = 0

	def score(self, vul: Vul) -> int:
		"The number of points the contract would score for the declarer"
		if vul == Vul.none:
			is_vul = False
		elif vul == Vul.ns:
			is_vul = (self.declarer in (Player.north, Player.south))
		elif vul == Vul.ew:
			is_vul = (self.declarer in (Player.east, Player.west))
		else:
			is_vul = True
		res = self.result
		if res < 0:
			if self.penalty == Penalty.none:
				if is_vul:
					return 100 * res
				else:
					return 50 * res
			elif self.penalty == Penalty.doubled:
				if is_vul:
					s = [-200] + [-300] * 12
					return sum(s[:-res])
				else:
					s = [-100] + [-200] * 2 + [-300] * 10
					return sum(s[:-res])
			elif self.penalty == Penalty.redoubled:
				if is_vul:
					s = [-400] + [-600] * 12
					return sum(s[:-res])
				else:
					s = [-200] + [-400] * 2 + [-600] * 10
					return sum(s[:-res])
		else:
			d, l = self.denom, self.level
			# Contract score
			if d == Denom.clubs or d == Denom.diamonds:
				score = 20 * l
			else:
				score = 30 * l
			if d == Denom.nt:
				score += 10
			score *= self.penalty
			# Game/part-score bonus
			if score >= 100:
				if is_vul: score += 500
				else: score += 300
			else:
				score += 50
			# Slam bonuses
			if l == 6:
				if is_vul: score += 750
				else: score += 500
			elif l == 7:
				if is_vul: score += 1500
				else: score += 750
			# Insult bonus
			if self.penalty == Penalty.doubled:
				score += 50
			elif self.penalty == Penalty.redoubled:
				score += 100
			# Overtrick bonus
			if self.penalty == Penalty.none:
				if self.denom == Denom.clubs or self.denom == Denom.diamonds:
					score += 20 * res
				else:
					score += 30 * res
			elif self.penalty == Penalty.doubled:
				if is_vul: score += 200 * res
				else: score += 100 * res
			else:
				if is_vul: score += 400 * res
				else: score += 200 * res
			return score

	def __repr__(self) -> str:
		return f'Contract("{self!s}")'

	def __str__(self) -> str:
		"A string representation of the contract e.g. 3NTW="
		s = f"{self.level}{self.denom.abbr}{self.declarer.abbr}{self.penalty.abbr}"
		return s + ("=" if self.result == 0 else f"{self.result:+d}")
