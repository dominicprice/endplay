"""
Main class of the interact module, which derives from :class:`Deal` but keeps track
of changes to its state.
"""

__all__ = ["InteractiveDeal"]

from endplay.types import Card, Deal, Player, Denom

class InteractiveDeal(Deal):
	"""
	A Deal which keeps track of changes made to it allowing actions to be undone.
	This is the basis of the various frontends to the interact package.
	"""
	def __init__(self, pbn: str = None, first: Player = Player.north, trump: Denom = Denom.nt):
		self._history = []
		super().__init__(pbn, first, trump)

	@Deal.trump.setter
	def trump(self, denom: Denom) -> None:
		self._history.append(("trump", self.trump))
		self._data.trump = denom

	def _undo_trump(self, denom):
		self._data.trump = denom

	@Deal.first.setter
	def first(self, player: Player) -> None:
		self._history.append(("first", self.first))
		self._data.first = player

	def _undo_first(self, player):
		self._data.first = player

	def play(self, card, fromHand: bool = True) -> None:
		if len(self.curtrick) == 3:
			toundo = ("play", (fromHand, self.first, self.curtrick, card))
		else:
			toundo = ("play", (fromHand,))
		super().play(card)
		self._history.append(toundo)
		
	def _undo_play(self, arg):
		if len(arg) == 1:
			self.unplay(arg)
		else:
			fromHand, first, trick, last_card = arg
			self._data.first = first
			for card in trick:
				super().play(card, False)
			if fromHand:
				super().__getitem__(self.first.rho).add(last_card)

	def unplay(self, toHand: bool = True) -> Card:
		card = super().unplay(toHand)
		hist = ("unplay", self.curplayer, card, toHand)
		self._history.append(hist)

	def _undo_unplay(self, player, card, toHand):
		super().play(card, toHand)

	def __setitem__(self, player, hand):
		hist = ("set", player, self[player])
		super().__setitem__(player, hand)
		self._history.append(hist)

	def _undo_set(self, player, pbn):
		super().__setitem__(player, pbn)

	def reset(self):
		"Undo all actions in the undo history"
		while self._history:
			self.undo()

	def checkpoint(self):
		"Clear undo history so that `reset` will bring the deal back to this state"
		self._history = []

	def undo(self):
		"Undo the previous action, if it changed the current deal"
		if self._history:
			action, *args = self._history.pop()
			getattr(self, f"_undo_{action}")(*args)
			return True
		else:
			return False