from __future__ import annotations

__all__ = ["Board"]

from endplay.types.deal import Deal
from endplay.types.contract import Contract
from endplay.types.vul import Vul
from endplay.types.player import Player
from endplay.types.bid import Bid
from endplay.types.card import Card
from typing import Optional, Any
from collections.abc import Iterable

class Board:
	"""
	Class representing a deal along with the play, auction and other table
	information

	:ivar deal: The deal at the table
	:vartype deal: Deal
	:ivar auction: The auction at the table
	:vartype auction: list[Bid]
	:ivar contract: The contract at the table
	:vartype contract: Contract
	:ivar play: The play history at the table
	:vartype play: list[Card]
	:ivar board_num: The board number of this deal
	:vartype board_num: int
	:ivar vul: The board vulnerability. If this isn't defined 
		(i.e. set to `None`) then it is deduced from `board_num`
	:vartype vul: Vul
	:ivar dealer: The board dealer. Similarly to `vul` this can 
		be deduced from `board_num`
	:vartype dealer: Player
	:ivar claimed: Flag indicating whether the play ended as a result
		of a claim
	:vartype claimed: bool
	:ivar info: A dictionary which contains arbitrary extra information
		about the board. The dictionary type used provided case-insensitive
		dot-access as a convenience (i.e. `board.info.event` and `board.info.Event`
		refer to the same object, but `board.info["event"]` and `board.info["Event"]`
		would be considered different). Tabular data can be stored here, any
		key ending with (but not equal to) `table` is treated as a table and its value 
		should be a dictionary containing two keys: `headers` with a list of column names, 
		and `rows` with a list of the rows. The column names can either be plain strings, 
		or dictionaries with the keys 
		
		* `ordering`: Either `"+"`, `"-"` or `None` depending of if the table is sorted 
			ascending, descending or unsorted with respect to this column
		* `name`: A string value with the name of the column
		* `minwidth`: The minimum width that values in this column should be
		* `alignment`: `"L"` or `"R"` depending on if this column should be left or right 
			aligned. Ignored unless `minwidth` is defined
	"""
	class Info(dict):
		"""
		Dictionary-like class which alows for case-insensitive dot-access,
		for example::

			info["Event"] = "WBF 2017"
			print(info.event) # WBF 2017
		"""
		def _find_key(self, key: str):
			key = key.casefold()
			for k in self:
				if k.casefold() == key:
					return k
			return None
		def __getattr__(self, attr: str) -> Any:
			key = self._find_key(attr)
			if key is not None:
				return self[key]
			return None
		def __setattr__(self, attr: str, value: Any) -> None:
			key = self._find_key(attr)
			if key is not None:
				self[key] = value
			else:
				self[attr] = value
		def __delattr__(self, attr: str) -> None:
			key = self._find_key(attr)
			if key is not None:
				del self[key]
			else:
				raise KeyError(attr)

	def __init__(self, 
		deal: Optional[Deal] = None,
		auction: Optional[Iterable[Bid]] = None,
		play: Optional[Iterable[Card]] = None,
		board_num: Optional[int] = None,
		*,
		vul: Optional[Vul] = None,
		dealer: Optional[Player] = None,
		contract: Optional[Contract] = None,
		claimed: bool = False,
		**kwargs):
		self.deal = deal.copy() if deal is not None else Deal()
		self.auction = list(auction) if auction is not None else []
		self.play = list(play) if play is not None else []
		self.board_num = board_num
		self._dealer = dealer
		self._vul = vul
		self._contract = contract
		self.claimed = claimed
		self.info = Board.Info(**kwargs)

	@property
	def dealer(self) -> Player:
		"""
		Dealer of the board. If not defined, then attempts to
		calculate based on the value of `board_num`
		"""
		if self._dealer is not None:
			return self._dealer
		elif self.board_num is not None:
			return Player.from_board(self.board_num)
		else:
			return None
	@dealer.setter
	def dealer(self, value: Player) -> None:
		self._dealer = value

	@property
	def vul(self) -> Vul:
		"""
		Vulnerability of the board. If not defined, then attempts
		to calculate based on the value of `board_num`
		"""
		if self._vul is not None:
			return self._vul
		elif self.board_num is not None:
			return Vul.from_board(self.board_num)
		else:
			return None
	@vul.setter
	def vul(self, value: Vul) -> None:
		self._vul = value

	@property
	def contract(self) -> Contract:
		"""
		The contract the board was played in. If not provided, then
		attempts to calculate based on the auction and play history.
		"""
		if self._contract is not None:
			return self._contract
		elif self.auction:
			c = Contract.from_auction(self.auction)
			if self.play:
				from endplay.utils.play import total_tricks, tricks_to_result
				c.result = tricks_to_result(
					total_tricks(self.play, self.deal.trump), 
					c.level)
		else:
			return None
	@contract.setter
	def contract(self, value: Contract) -> None:
		self._contract = value