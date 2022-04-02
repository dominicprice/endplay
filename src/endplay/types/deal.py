from __future__ import annotations

__all__ = ["Deal"]

import sys
import json as _json
from typing import Union, Optional
from collections.abc import Iterable, Iterator
import ctypes
from endplay.types.denom import Denom
from endplay.types.rank import AlternateRank
from endplay.types.player import Player
from endplay.types.card import Card
from endplay.types.hand import Hand
from endplay.types.vul import Vul
import endplay._dds as _dds

class Deal:
	"""
	Class representing a bridge deal. The class keeps track of the four hands
	at the table, as well as

	* The player on initial lead to the current trick in `Deal.first`
	* The trump suit the deal is played in in `Deal.trump`
	* The cards played to the current trick in `Deal.curtrick`
	"""
	def __init__(self, 
		pbn: str = None, 
		first: Player = Player.north, 
		trump: Denom = Denom.nt, 
		*, 
		complete_deal: bool = False):
		self._data = _dds.deal()
		self.clear()
		self._data.first = first
		self._data.trump = trump
		if pbn is not None:
			if len(pbn) > 2 and pbn[1] == ":":
				start, hands = Player.find(pbn[0]), pbn[2:].split()
			for player, hand in zip(Player.iter_from(start), hands):
				self[player] = hand
			if complete_deal:
				self.complete_deal()
		
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
			# Lazy import to avoid circular import
			from endplay.utils.play import trick_winner
			if fromHand and not self[self.first.rho].remove(card):
				raise RuntimeError("Trying to play card not in hand")
			self.first = trick_winner(self.curtrick + [card], self.first, self.trump)
			for i in range(3):
				self._data.currentTrickRank[i] = 0
				
	def unplay(self, toHand: bool = True) -> Card:
		"""
		Unplay the last card played to the current trick. Throws a RuntimeError if the current
		trick is empty

		:param toHand: If true then the card is returned to the hand of the player who played
			it to the trick
		:return: The card that was picked up
		"""
		for i in reversed(range(3)):
			suit, rank = self._data.currentTrickSuit[i], self._data.currentTrickRank[i]
			if rank != 0:
				self._data.currentTrickRank[i] = 0
				card = Card(suit=Denom(suit), rank=AlternateRank(rank).to_standard())
				if toHand:
					self[self.first.next(i)].add(card)
				return card
		else:
			raise RuntimeError("No cards to unplay")

	def complete_deal(self) -> None:
		"""
		If there is a player with no cards, deal any cards which do not appear in anyone else's
		hand to that player
		"""
		remaining = Hand("AKQJT98765432.AKQJT98765432.AKQJT98765432.AKQJT98765432")
		missing_hand = None
		for player, hand in self:
			if len(hand) == 0:
				if missing_hand:
					raise ValueError("Cannot complete a deal with more than one missing hand")
				missing_hand = player
			else:
				for card in hand:
					remaining.remove(card)
		if missing_hand is not None:
			if len(remaining) != 13:
				raise ValueError("Cannot complete a deal with more than 13 undealt cards")
			self[missing_hand] = remaining

	@staticmethod
	def from_pbn(pbn: str) -> 'Deal':
		"""
		Clear all hands and the current trick, and replace with the cards in a PBN string

		:param pbn: A PBN string, e.g. "N:974.AJ3.63.AK963 K83.K9752.7.8752 AQJ5.T864.KJ94.4 T62.Q.AQT852.QJT"
		"""
		return Deal(pbn)
			
	def to_pbn(self) -> str:
		"Return a PBN string representation of the deal"
		return 'N:' + ' '.join(str(self[player]) for player in Player)

	@staticmethod
	def from_json(json: Union[str, dict]):
		if isinstance(json, str):
			json = _json.loads(json)
		deal = Deal()
		deal.north = json["north"]
		deal.east = json["east"]
		deal.south = json["south"]
		deal.west = json["west"]
		deal.first = Player.find(json["first"])
		deal.trump = Denom.find(json["trump"])
		for card in json["curtrick"]:
			deal.play(card, False)
		return deal

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

	@staticmethod
	def from_lin(lin: str, complete_deal: bool = True):
		"""
		Construct a deal from a LIN format deal string. 

		:param complete_deal: If True, then add remaining cards to the last hand if it is
			omitted from the input string (which is done by default for files downloaded
			from BBO)
		"""
		if lin[0] in "1234":
			hands = lin[1:].split(",")
		else:
			hands = lin.split(",")
		deal = Deal()
		for player, hand in zip(Player.iter_from(Player.south), hands):
			deal[player] = Hand.from_lin(hand)
		if complete_deal:
			deal.complete_deal()
		return deal

	def to_lin(self, dealer: Optional[Player] = None, complete_deal: bool = False) -> str:
		"""
		Convert a deal to LIN representation as used by BBO

		:param dealer: If provided, append the dealer (in LIN format) to the returned string
		:param complete_deal: If False, omit the last hand from the string. This is the default
			for files created by BBO.
		"""
		if dealer is not None:
			lin = str(dealer.to_lin())
		lin += self[Player.south].to_lin() + ","
		lin += self[Player.west].to_lin() + ","
		lin += self[Player.north].to_lin() + ","
		if complete_deal:
			lin += self[Player.east].to_lin()
		return lin

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
		for _, hand in self:
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
		for _, hand in self:
			hand.clear()
		while self.curtrick:
			self.unplay(False)

	def pprint(self, 
		board_no: int = None, 
		exclude: list[Player] = [], 
		stream=sys.stdout,
		*,
		vul: Optional[Vul] = None,
		dealer: Optional[Player] = None) -> None:
		"""
		Print the deal in a hand diagram format. 

		:param board_no: If provided, the hand diagram will display the board
			number, vulnerability and dealer in the top-left corner
		"""
		spacing = " " * 13
		played_cards = ["  "] * 4
		prefixes = ["    ^", "       >", "    v", "  <"]
		titles = [ spacing ] * 4
		if board_no is not None:
			titles[0] = f"Board {board_no}".center(13)
			if vul is None: vul = Vul.from_board(board_no)
			if dealer is None: dealer = Player.west.next(board_no)
		if vul is not None:
			titles[1] = f"Vul {vul.abbr}".center(13)
		if dealer is not None:
			titles[2] = f"{dealer.abbr} deals".center(13)
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
		return any(card in hand for _, hand in self)
	
	def __iter__(self) -> Iterator[Player, Hand]:
		":return: An iterator over the north, east, south and west hands respectively"
		yield from ((player, self[player]) for player in Player)

	def __getitem__(self, player: Player) -> Hand:
		":return: The specified hand"
		return Hand(self._data.remainCards[player])

	def __setitem__(self, player: Player, hand: Hand) -> None:
		"Set the hand to the specified hand, which may be in the format of a PBN string"
		if isinstance(hand, str):
			hand = Hand(hand)
		self._data.remainCards[player] = hand._data

	def compare(self, other: Deal, hands_only: bool = False) -> bool:
		cmp = _dds._libc.memcmp
		if cmp(self._data.remainCards, other._data.remainCards, len(self._data.remainCards)):
			return False
		if not hands_only:
			if self._data.trump != other._data.trump:
				return False
			if self._data.first != other._data.first:
				return False
			if cmp(self._data.currentTrickSuit, other._data.currentTrickSuit, len(self._data.currentTrickSuit)):
				return False
			if cmp(self._data.currentTrickRank, other._data.currentTrickRank, len(self._data.currentTrickRank)):
				return False
		return True

	def __eq__(self, other: Deal) -> bool:
		return self.compare(other)

	def __repr__(self) -> str:
		return f"Deal('{self!s}')"

	def __str__(self) -> str:
		":return: A PBN string representation of the deal"
		return self.to_pbn()
