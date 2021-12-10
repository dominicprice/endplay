"Parser for BridgeBase LIN files"

from __future__ import annotations

__all__ = [ "LINParser" ]

from typing import TextIO
from endplay.types import Deal, Bid, Vul, Card, Player, Board, Contract
from endplay.utils import tricks_to_result, total_tricks, unescape_suits

class LINParser:
	def __init__(self):
		pass

	def parse_line(self, line: str) -> Board:
		deal = None
		auction = []
		play = []
		board_num = None
		dealer = None
		vul = None
		contract = None
		info = {}

		elems = line.split("|")
		pairs = [(a, b) for a, b in zip(elems[::2], elems[1::2])]
		for key, value in pairs:
			key, value = key.strip(), value.strip()
			if key == "st":
				continue
			elif key == "pn":
				# Player names are comma separated starting from south
				info["names"] = {p: n for p, n in Player.south.enumerate(value.split(","))}
			elif key == "md":
				# Marks deal, starts with dealer then comma separated hands
				dealer = Player.from_lin(int(value[0]))
				deal = Deal.from_lin(value, complete_deal = True)
			elif key == "sv":
				# Marks vulnerability
				vul = Vul.from_lin(value)
			elif key == "ah":
				# Marks board number in format 'Board N'
				board_num = int(value[5:])
			elif key == "mb":
				# Marks a bid
				auction.append(Bid(value))
			elif key == "an":
				# Marks an alert for the previous bid
				auction[-1].alert = unescape_suits(value)
			elif key == "pc":
				# Marks a card in the play section
				play.append(Card(value))
			elif key == "pg":
				# Signifies end of play
				continue
			elif key == "mc":
				# Marks that tricks were claimed
				info["claimed"] = True
				if contract is None:
					contract = Contract.from_auction(auction)
					contract.result = tricks_to_result(int(value), contract.level)
			else:
				info[key] = value
		# ensure there is a contract if there was an auction
		if contract is None and (dealer is not None and len(auction) > 0):
			contract = Contract.from_auction(dealer, auction)
			if play:
				tricks = total_tricks(play, contract.denom)
				contract.result = tricks_to_result(int(tricks), contract.level)
		# make sure 'first' and 'trump' in deal are set correctly if there is
		# a contract
		if contract is not None:
			deal.first = contract.declarer.lho
			deal.trump = contract.denom
		return Board(deal, auction, play, board_num, vul=vul, dealer=dealer, contract=contract, **info)

	def parse_string(self, lin: str) -> list[Board]:
		boards = []
		for line in lin.splitlines():
			boards.append(self.parse_line(line))
		return boards

	def parse_file(self, f: TextIO) -> list[Board]:
		boards = []
		for line in f:
			boards.append(self.parse_line(line))
		return boards