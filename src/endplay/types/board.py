from __future__ import annotations

__all__ = ["Board"]

from endplay.types.deal import Deal
from endplay.types.contract import Contract
from endplay.types.vul import Vul
from endplay.types.player import Player
from endplay.types.bid import Bid
from endplay.types.card import Card
from typing import Optional
from collections.abc import Iterable

class Board:
	def __init__(self, 
		deal: Optional[Deal] = None,
		auction: Optional[Iterable[Bid]] = None,
		play: Optional[Iterable[Card]] = None,
		board_num: Optional[int] = None,
		*,
		vul: Optional[Vul] = None,
		dealer: Optional[Player] = None,
		contract: Optional[Contract] = None,
		**kwargs):
		self.deal = deal.copy() if deal is not None else Deal()
		self.auction = list(auction) if auction is not None else []
		self.play = list(play) if play is not None else []
		self.board_num = board_num
		self._dealer = dealer
		self._vul = vul
		self._contract = contract
		self.info = dict(**kwargs)

	@property
	def dealer(self) -> Player:
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
		if self._contract is not None:
			return self._contract
		elif self.auction:
			c = Contract.from_auction(self.auction)
			if self.play:
				from endplay.utils import total_tricks, tricks_to_result
				c.result = tricks_to_result(
					total_tricks(self.play, self.deal.trump), 
					c.level)
		else:
			return None
	@contract.setter
	def contract(self, value: Contract) -> None:
		self._contract = value