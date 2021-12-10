"""
Algorithms for detecting play techniques
"""

from __future__ import annotations

__all__ = ["detect_play", "SingleFinesse", "PlayTechniqueBase"]

from endplay.types import Deal, Card, Rank, SuitHolding

class NoMatch(Exception):
	pass

def rank_below(rank: Rank, holding: SuitHolding):
	"Return the rank just below `rank` in `holding`. Returns `None` if `rank` is the first card"
	prev = None
	for r in holding:
		if r == rank:
			return prev
		prev = r
	raise ValueError(f"{rank} not found in holding")

def rank_above(rank: Rank, holding: SuitHolding):
	"Return the rank just above `rank` in `holding`. Returns `None` if `rank` is the last card"
	foundRank = None
	for r in holding:
		if r == rank:
			foundRank = True
		elif foundRank:
			return r
	if foundRank:
		return None
	raise ValueError(f"{rank} not found in holding")

def rank_equivalent(rankA: Rank, rankB: Rank, remaining: SuitHolding):
	"""
	Return true if `cardA` and `cardB` are equivalent cards, given that
	the only cards of that suit left in the deal are in `remaining`
	"""
	foundA = False
	for rank in remaining:
		if rank == rankA:
			foundA = True
		elif foundA:
			return rank == rankB
	raise ValueError(f"{rankA} not found in remaining cards")


class PlayTechniqueBase:
	def __init__(self):
		self.match = False
		self.exception = None

	def __bool__(self):
		return self.match

	def match(self, deal, trick):
		try:
			if len(trick) != 4:
				raise ValueError("`trick` must contain four cards")
			for i, card in enumerate(trick):
				if not isinstance(card, Card):
					trick[i] = Card(card)
			self._match(deal, trick)
		except NoMatch as e:
			self.exception = e
		return self.match


class Finesse(PlayTechniqueBase):
	def __init__(self):
		super().__init__()
		self.onside = False
		self.lho_covered = False
		self.rho_covered = False

class SimpleFinesse(PlayTechniqueBase):
	def __init__(self):
		super().__init__()
		self.is_onside = False
		self.lho_covered = False
		self.rho_covered = False

	def _match(self, deal: Deal, trick: list[Card]):
		# First three cards must be the same suit
		suit = trick[0].suit
		if suit != trick[1].suit or suit != trick[2].suit:
			raise NoMatch("First three cards must be of the same suit")
		# Get all cards in the suit
		lho = deal[deal.first.lho][suit]
		rho = deal[deal.first.rho][suit]
		opps = lho.copy()
		opps.extend(rho)
		leader = deal[deal.first][suit]

		# Check for the following scenarios:
		# - 

		leader.extend(deal[deal.first.partner][suit])
		total = opps.copy()
		total.extend(leader)
		# Find cards in the opponent's hands where the leader has the
		# card directly above/below


def detect_play(deal: Deal, play_history: list[Card], techniques: list[PlayTechniqueBase]=None):
	if techniques is None:
		techniques = [SimpleFinesse]

	res = []
	for technique in techniques:
		match = technique()
		if technique.match(deal, play_history):
			res.append(match)
	return res