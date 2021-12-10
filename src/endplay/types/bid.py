from endplay.types.denom import Denom
from endplay.types.penalty import Penalty
from typing import Optional

class Bid:
	def __init__(self, 
		name: Optional[str] = None, 
		*, 
		denom: Optional[Denom] = None, 
		level: Optional[int] = None, 
		penalty: Optional[Penalty] = None,
		alert: Optional[str] = None):
		self.alert = alert
		if name is not None:
			name = name.strip().lower()
			try:
				self.penalty = Penalty.find(name)
			except ValueError:
				level, denom = name[0], name[1]
				self.level = int(level)
				self.denom = Denom.find(denom)
		elif penalty is not None:
			self.penalty = penalty
		else:
			n_defined = (level is None) + (denom is None)
			if n_defined == 0:
				self.penalty = Penalty.passed
			elif n_defined == 1:
				raise ValueError("Only one of `denom` or `level` provided")
			else:
				self.level, self.denom = level, denom

	def is_contract(self):
		"""
		Returns True if the bid names a contract, i.e. is not a
		pass, double or redouble
		"""
		return hasattr(self, "denom")

	def __repr__(self):
		if hasattr(self, "penalty"):
			return f"Bid(penalty={self.penalty!r}, alert={self.alert!r})"
		else:
			return f"Bid(denom={self.denom!r}, level={self.level!r}, alert={self.alert!r})"

	def __str__(self):
		if hasattr(self, "penalty"):
			res = self.penalty.attr or "p"
		else:
			res = f"{self.level}{self.denom.abbr}"
		if self.alert is not None:
			res += "*"
		return res