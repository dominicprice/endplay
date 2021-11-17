from __future__ import annotations

__all__ = ["Deal"]

import sys
import re
import json as _json
from typing import Iterable, Iterator, Union, Optional
import ctypes
from endplay.types.denom import Denom
from endplay.types.rank import Rank, AlternateRank
from endplay.types.player import Player
from endplay.types.card import Card
from endplay.types.suitholding import SuitHolding
from endplay.types.hand import Hand
from endplay.types.vul import Vul
import endplay._dds as _dds

class Deal:
	def __init__(self, pbn: str = None, first: Player = Player.north, trump: Denom = Denom.nt):
		self._data = _dds.deal()
		self.clear()
		self.first = first
		self.trump = trump
		if pbn is not None:
			self.from_pbn(pbn)
		
	def __copy__(self) -> 'Deal':
		other = Deal()
		other._data.trump = self._data.trump
		other._data.first = self._data.first
		sizeOfTrick = ctypes.sizeof(ctypes.c_int) * 3
		sizeOfCards = ctypes.sizeof(ctypes.c_uint) * 4 * 4
		ctypes.memmove(other._data.currentTrickSuit, self._data.currentTrickSuit, sizeOfTrick)
		ctypes.memmove(other._data.currentTrickRank, self._data.currentTrickRank, sizeOfTrick)
		ctypes.memmove(other._data.remainCards, self._data.remainCards, sizeOfCards)
		return other

	def copy(self) -> 'Deal':
		"Return a new copy of this deal"
		return self.__copy__()

	@property
	def trump(self) -> Denom:
		"The trump suit the deal is being played in"
		return Denom(self._data.trump)
	@trump.setter
	def trump(self, denom: Denom) -> None:
		self._data.trump = denom
		
	@property
	def first(self) -> Player:
		"The player to lead the first card to the current trick"
		return Player(self._data.first)
	@first.setter
	def first(self, player) -> None:
		self._data.first = player
		
	@property
	def curplayer(self) -> Player:
		"The player to play the next card to the current trick"
		return Player(self._data.first).next(len(self.curtrick))
				
	@property
	def curhand(self) -> Hand:
		"The hand of the `curplayer`"
		return self[self.curplayer]
				
	@property
	def north(self) -> Hand:
		"The north hand"
		return self[Player.north]
	@north.setter
	def north(self, hand: Hand) -> None:
		self[Player.north] = hand
		
	@property
	def east(self) -> Hand:
		"The east hand"
		return self[Player.east]
	@east.setter
	def east(self, hand: Hand) -> None:
		self[Player.east] = hand
		
	@property
	def south(self) -> Hand:
		"The south hand"
		return self[Player.south]
	@south.setter
	def south(self, hand: Hand) -> None:
		self[Player.south] = hand
		
	@property
	def west(self) -> Hand:
		"The west hand"
		return self[Player.west]
	@west.setter
	def west(self, hand: Hand) -> None:
		self[Player.west] = hand
		
	@property	
	def curtrick(self) -> list[Card]:
		"Return a list of cards played to the current trick"
		trick = []
		for i in range(3):
			suit, rank = self._data.currentTrickSuit[i], self._data.currentTrickRank[i]
			if rank == 0:
				break
			trick.append(Card(suit=Denom(suit), rank=AlternateRank(rank).to_standard()))
		return trick
		
	def play(self, card: Card, fromHand: bool = True) -> None:
		"""
		Play a card to the current trick. If the played card completes the trick then the entire
		trick is cleared and `first` is set to the played who won the trick using `trump` as the
		trumps suit

		:param card: The cad to be played
		:param fromHand: If true then the card will be removed from the hand of the player who is to
			play to the trick next and throw a RuntimeError if they do not hold this card.
		"""
		if isinstance(card, str):
			card = Card(card)
		for i in range(3):
			if self._data.currentTrickRank[i] == 0:
				if fromHand and not self[self.first.next(i)].remove(card):
					raise RuntimeError("Trying to play card not in hand")
				self._data.currentTrickRank[i] = card.rank.to_alternate()
				self._data.currentTrickSuit[i] = card.suit
				break
		else:
			# Playing final card to a trick: Calculate winner, update first and clear current trick
			if fromHand and not self[self.first.rho].remove(card):
				raise RuntimeError("Trying to play card not in hand")
			trick = self.curtrick + [card]
			winner, topcard = self.first, trick[0]
			for i in range(1, 4):
				if trick[i].suit == topcard.suit and trick[i].rank > topcard.rank:
					winner, topcard = self.first.next(i), trick[i]
				elif trick[i].suit == self.trump:
					winner, topcard = self.first.next(i), trick[i]
			self.first = winner
			for i in range(3):
				self._data.currentTrickRank[i] = 0
				
	def unplay(self, toHand: bool = True) -> None:
		"""
		Unplay the last card played to the current trick. Throws a RuntimeError if the current
		trick is empty

		:param toHand: If true then the card is returned to the hand of the player who played
			it to the trick
		"""
		for i in reversed(range(3)):
			suit, rank = self._data.currentTrickSuit[i], self._data.currentTrickRank[i]
			if rank != 0:
				self._data.currentTrickRank[i] = 0
				if toHand:
					card = Card(suit=Denom(suit), rank=AlternateRank(rank).to_standard())
					self[self.first.next(i)].add(card)
				break
		else:
			raise RuntimeError("No cards to unplay")

	def from_pbn(self, pbn: str) -> None:
		"""
		Clear all hands and the current trick, and replace with the cards in a PBN string

		:param pbn: A PBN string, e.g. "N:974.AJ3.63.AK963 K83.K9752.7.8752 AQJ5.T864.KJ94.4 T62.Q.AQT852.QJT"
		"""
		if len(pbn) > 2 and pbn[1] != ":":
			pbn = "N:" + pbn
		hands = re.match(r"([NESW]):(\S+)\s(\S+)\s(\S+)\s(\S+)", pbn)
		if not hands:
			raise ValueError(f"Could not parse pbn string '{pbn}'")
		for i, player in enumerate(Player.iter_from("NESW".index(hands.group(1))), 2):
			self[player].from_pbn(hands.group(i))
			
	def to_pbn(self) -> str:
		"Return a PBN string representation of the deal"
		return 'N:' + ' '.join(str(self[player]) for player in Player)

	def from_json(self, json: Union[str, dict]):
		if isinstance(json, str):
			json = _json.loads(json)
		self.north = json["north"]
		self.east = json["east"]
		self.south = json["south"]
		self.west = json["west"]
		self.first = Player.find(json["first"])
		self.trump = Denom.find(json["trump"])
		for card in json["curtrick"]:
			self.play(card, False)

	def to_json(self, indent: Optional[int] = None) -> str:
		"Encode the data as a JSON string"
		d = {
			"north": self.north.to_pbn(),
			"east": self.east.to_pbn(),
			"south": self.south.to_pbn(),
			"west": self.west.to_pbn(),
			"curtrick": [str(card) for card in self.curtrick],
			"first": self.first.name,
			"trump": self.trump.name
		}
		return _json.dumps(d, indent=indent)

	def to_LaTeX(self, board_no: Optional[int] = None, exclude: Iterable[Player] = [], ddtable: bool = False) -> str:
		"Return a LaTeX representation of the hand"
		mkhand = lambda p: self[p].to_LaTeX() if p not in exclude else ""
		res = r"\begin{tabular}{c c c}"
		if board_no is not None:
			res += r"\begin{tabular}{c}"
			res += f"Board {board_no}\\\\Vul "
			vul = Vul.from_board(board_no)
			if vul == Vul.none: res += "none"
			elif vul == Vul.both: res += "all"
			elif vul == Vul.ns: res += "N/S"
			else: res += "E/W"
			res += f"\\\\{Player.west.next(board_no).abbr} deals\\\\"
			res += r"\end{tabular}"
		res += " & " + mkhand(Player.north) + " & \\\\"
		res += mkhand(Player.west) + r" & \fbox{\begin{tabular}{c c c}&N&\\W&&E\\&S&\end{tabular}} & "
		res += mkhand(Player.east) + r"\\ & " + mkhand(Player.south) + " & "
		if ddtable:
			from endplay.dds.ddtable import calc_dd_table
			res += r"\footnotesize{\setlength{\tabcolsep}{2pt} " + calc_dd_table(self).to_LaTeX() + "}"
		res += r"\end{tabular}"
		return res

	def to_hand(self) -> Hand:
		"Return a new hand containing the contents of all four hands in the deal"
		res = Hand()
		for hand in self:
			res.extend(hand)
		return res

	def rotate(self, n: int) -> None:
		"Rotate clockwise by n quarter-turns, e.g. with n=1 NESW -> WNES"
		n %= 4
		if n == 0:
			return
		rc = self._data.remainCards
		# tuple assignment doesn't work for ctypes types so we use tmp + memmove
		# also as the array is only 4 elements it's not too much effort to treat
		# the four cases separately for a bit of extra efficiency
		l = ctypes.sizeof(ctypes.c_uint) * 4
		tmp = (ctypes.c_uint * 4).from_buffer_copy(rc[0])
		if n == 1: # nesw -> wnes
			ctypes.memmove(rc[0], rc[3], l)
			ctypes.memmove(rc[3], rc[2], l)
			ctypes.memmove(rc[2], rc[1], l)
			ctypes.memmove(rc[1], tmp, l)
		elif n == 2: # nesw -> swne
			self.swap(0, 2)
			self.swap(1, 3)
		elif n == 3: # nesw -> eswn:
			ctypes.memmove(rc[0], rc[1], l)
			ctypes.memmove(rc[1], rc[2], l)
			ctypes.memmove(rc[2], rc[3], l)
			ctypes.memmove(rc[3], tmp, l)

	def swap(self, player_a: Player, player_b: Player) -> None:
		"Swap the specified hands"
		rc = self._data.remainCards
		# tuple assignment doesn't work for ctypes types so we use tmp + memmove
		l = ctypes.sizeof(ctypes.c_uint) * 4
		tmp = (ctypes.c_uint * 4).from_buffer_copy(rc[player_a])
		ctypes.memmove(rc[player_a], rc[player_b], l)
		ctypes.memmove(rc[player_b], tmp, l)

	def clear(self) -> None:
		"Clear all hands and the cards in the current trick"
		for player in self:
			player.clear()
		while self.curtrick:
			self.unplay(False)

	def pprint(self, board_no: int = None, exclude: list[Player] = [], stream=sys.stdout) -> None:
		"""
		Print the deal in a hand diagram format. 

		:param board_no: If provided, the hand diagram will display the board
			number, vulnerability and dealer in the top-left corner
		"""
		spacing = " " * 13
		played_cards = ["  "] * 4
		prefixes = ["    ^", "       >", "    v", "  <"]
		if board_no:
			titles = [ 
				f"Board {board_no}".center(13), 
				f"Vul {Vul.from_board(board_no).abbr}".center(13), 
				f"{Player.west.next(board_no).abbr} deals".center(13),
				spacing]
		else:
			titles = [ spacing ] * 4
		for player, card in zip(Player.iter_from(self.first), self.curtrick):
			played_cards[player] = prefixes[player] + str(card)
		for title, suit in zip(titles, Denom.suits()):
			n = (str(self[Player.north][suit]) or "---") if Player.north not in exclude else ""
			print(title, n, file=stream)
		for player, suit in zip([Player.find(p) for p in "news"], Denom.suits()):
			w = (str(self[Player.west][suit]) or "---") if Player.west not in exclude else ""
			e = (str(self[Player.east][suit]) or "---") if Player.east not in exclude else ""
			print(w.ljust(13), played_cards[player].ljust(13), e, file=stream)
		for suit in Denom.suits():
			s = (str(self[Player.south][suit]) or "---") if Player.south not in exclude else ""
			print(spacing, s, file=stream)
			
	def __contains__(self, card: Card) -> bool:
		":return: True if card is in the current deal"
		return any(card in hand for hand in self)
	
	def __iter__(self) -> Iterator[Hand]:
		":return: An iterator over the north, east, south and west hands respectively"
		yield from (self[player] for player in Player)

	def __getitem__(self, player: Player) -> Hand:
		":return: The specified hand"
		return Hand(self._data.remainCards[player])

	def __setitem__(self, player: Player, hand: Hand) -> None:
		"Set the hand to the specified hand, which may be in the format of a PBN string"
		if isinstance(hand, str):
			hand = Hand(hand)
		self._data.remainCards[player] = hand._data

	def __repr__(self) -> str:
		return f"Deal('{self!s}')"

	def __str__(self) -> str:
		":return: A PBN string representation of the deal"
		return self.to_pbn()
