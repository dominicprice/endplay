__all__ = ["InteractiveDeal", "interact"]

import cmd
from typing import Optional
from endplay.dealer import generate_deal
from endplay.types import Card, Deal, Vul, Player, Denom
from endplay.dds import solve_board, calc_dd_table, analyse_play, par
from endplay.evaluate import hcp
import shlex

class InteractiveDeal(cmd.Cmd):
	def __init__(self, deal: Optional[Deal] = None):
		if deal is not None:
			self.deal = deal
		else:
			self.deal = generate_deal()
		self.needs_printing = True
		self.undo_history = []
		self.board_no = 1
		super().__init__()
		
	def onecmd(self, line):
		try:
			super().onecmd(line)
		except Exception as e:
			print("Encountered an unexpected error while executing:", e)
		
	def cmdloop(self, intro=None):
		self.postcmd(False, "")
		try:
			super().cmdloop(intro)
		except KeyboardInterrupt:
			return

	def emptyline(self):
		pass
		
	def postcmd(self, stop, line):
		if self.needs_printing:
			print()
			self.deal.pprint(self.board_no)
			self.needs_printing = False
		self.prompt = self.deal.first.abbr + "> "
		return stop
		
	def do_ddtable(self, arg):
		"Calculate the double dummy table for the current deal"
		if len(self.deal.curtrick) != 0:
			print("No cards must be played to the current trick for this action")
			return
		table = calc_dd_table(self.deal)
		table.pprint()
		
	def do_play(self, arg):
		"""
		Play the listed cards.
		Example 1: play SA
		Example 2: play HQ S5 H2
		"""
		args = arg.split()
		for a in args:
			try:
				card = Card(a)
			except ValueError:
				print(f"Could not parse `{a}` as a card name")
				return
			try:
				if len(self.deal.curtrick) == 3:
					toundo = ("trick", self.deal.first, self.deal.curtrick)
				else:
					toundo = ("play", )
				self.deal.play(card)
				self.undo_history.append(toundo)
				self.needs_printing = True
			except RuntimeError:
				print(f"Was unable to play the {card} at this time; is it in the player's hand?")
		
	def undo_play(self):
		self.deal.unplay()
		
	def undo_trick(self, first, trick):
		self.deal.first = first
		for player, card in zip(Player.iter_from(first), trick):
			self.deal[player].add(card)
			self.deal.play(card)
		
	def do_reset(self, arg):
		"Reset the deal to its original state"
		while self.undo_history:
			self.do_undo(None)
		
	def do_checkpoint(self, arg):
		"Erase the undo history so that reset will take you back to this point"
		self.undo_history = []
		
	def do_set(self, arg):
		"""
		Set a hand to given PBN string
		Example: set S AQ85.532..JT92
		No error checking for duplicate cards or incorrect number of cards is performed.
		"""
		if len(self.deal.curtrick) != 0:
			print("No cards must be played to the current trick for this action")
			return
		args = arg.split()
		if len(args) != 2:
			print(f"Expected two arguments (player and PBN string), got {len(args)}")
		try:
			player = Player.find(args[0])
		except ValueError:
			print(f"Could not parse {args[0]} as player name")
			return
		try:
			cur_pbn = str(self.deal[player])
			self.deal[player].from_pbn(args[1])
			self.undo_history.append(("set", player, cur_pbn))
			self.needs_printing = True
		except RuntimeError:
			print(f"Invalid PBN string: `{args[0]}`")
		
	def undo_set(self, player, pbn):
		self.deal[player].from_pbn(pbn)

	def do_solve(self, arg):
		"""
		Display the double-dummy maximum number of tricks playing each card in the current
		player's hand can yield.
		"""
		res = {}
		for card, tricks in solve_board(self.deal):
			if tricks in res:
				res[tricks].append(card)
			else:
				res[tricks] = [card]
		for tricks, cards in res.items():
			print(f"{tricks}:", "  ".join(str(c) for c in cards))
		
	def do_redeal(self, arg):
		"""
		Redeal the hand to the given PBN string (or an empty string for a blank deal)
		Example 1: redeal
		Example 2: redeal N:95..A. 8.5.Q. .QT5.. Q..T4.
		"""
		hist = ("redeal", str(self.deal), self.deal.curtrick, self.deal.trump, self.deal.first)
		if arg:
			try:
				self.deal.from_pbn(arg)
				self.undo_history.append(hist)
				self.needs_printing = True
			except RuntimeError:
				print(f"Invalid PBN string: `{arg}`")
		else:
			self.deal = Deal()
			self.undo_history.append(hist)
			self.needs_printing = True

	def do_shuffle(self, arg):
		"""
		Generate a random deal satisfying the given constraints.
		Example 1: shuffle
		Example 2: shuffle hcp(north) > hcp(south)
		"""
		hist = ("redeal", str(self.deal), self.deal.curtrick, self.deal.trump, self.deal.first)
		if arg:
			try:
				self.deal = generate_deal(arg)
				self.undo_history.append(hist)
				self.needs_printing = True
			except RuntimeError:
				print(f"Could not generate deal satisfying this constraint")
		else:
			self.deal = generate_deal()
			self.undo_history.append(hist)
			self.needs_printing = True

	def undo_redeal(self, pbn, curtrick, trump, first):
		self.deal = Deal(pbn)
		self.deal.first = first
		self.deal.trump = trump
		for player, card in zip(Player.iter_from(first), curtrick):
			self.deal[player].add(card)
			self.deal.play(card)
		
	def do_first(self, arg):
		"""
		If no argument is provided, display the position of the player to play the first card to
		the current trick. If a position is given, set that seat to be on lead
		Example 1: first
		Example 2: first W
		"""
		if not arg:
			print(self.deal.first.name)
			return
			
		if len(self.deal.curtrick) != 0:
			print("No cards must be played to the current trick for this action")
			return
		try:
			player = Player.find(arg)
			self.undo_history.append(("first", self.deal.first))
			self.deal.first = player
		except ValueError:
			print(f"Unrecognised player: {arg}")
		
	def undo_first(self, player):
		self.deal.first = arg

	def do_board(self, arg):
		"""
		If no argument is provided, display the board number. If a number is given, set the
		board number to this.
		Example 1: board
		Example 2: board 12
		"""
		if not arg:
			print(self.board_no)
		else:
			self.board_no = int(arg)
			self.needs_printing = True
		
	def do_trump(self, arg):
		"""
		If no argument is provided, display the trump suit of the current deal. If a suit is
		given, set the trump suit to this.
		Example 1: trump
		Example 2: trump NT
		"""
		if not arg:
			print(self.deal.trump.name)
			return
			
		if len(self.deal.curtrick) != 0:
			print("No cards must be played to the current trick for this action")
			return
		denom = Denom.find(arg)
		self.undo_history.append(("trump", self.deal.trump))
		self.deal.trump = denom
		
	def undo_trump(self, denom):
		self.deal.trump = denom

	def do_hcp(self, arg):
		player = Player.find(arg)
		print(hcp(self.deal[player]))
		
	def do_analyse(self, arg):
		"""
		If no arguments are provided, display the double dummy results of playing each card
		in the hand currently on lead. If a list of cards are provided, display the double
		dummy results for each card as it is played
		"""
		play = [Card(c) for c in arg.split()]
		first, *rest = analyse_play(self.deal, play)
		print("  ", first)
		for card, tricks in zip(play, rest):
			print(card, tricks)

	def do_par(self, arg):
		"""
		Calculate the par contract and score for the board using the first player as the
		dealer
		"""
		vul = Vul.from_board(self.board_no)
		dealer = Player.west.next(self.board_no)
		p = par(self.deal, vul, self.deal.first)
		print(f"Par score: {p.score}")
		for contract in p:
			print(" -", contract)

	def do_display(self, arg):
		"Displays the current deal"
		self.needs_printing = True

	def do_pbn(self, arg):
		"Displays the current deal as a PBN string"
		print(str(self.deal))
		
	def do_undo(self, arg):
		"Undo the previous action, if it changed the current deal"
		if self.undo_history:
			action, *args = self.undo_history.pop()
			if action == 'play':
				self.undo_play()
				self.needs_printing = True
			elif action == 'trick':
				self.undo_trick(*args)
				self.needs_printing = True
			elif action == 'redeal':
				self.undo_redeal(*args)
				self.needs_printing = True
			elif action == 'set':
				self.undo_set(*args)
				self.needs_printing = True
			elif action == 'first':
				self.undo_first(args)
			elif action == 'trump':
				self.undo_trump(args)
		else:
			print("Nothing to undo")
			
	def do_exit(self, arg):
		"Exits the interaction"
		raise KeyboardInterrupt
		
def interact(deal: Optional[Deal] = None) -> None:
	i = InteractiveDeal(deal)
	i.cmdloop()
