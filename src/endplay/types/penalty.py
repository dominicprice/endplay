__all__ = ["Penalty"]

from enum import IntEnum

class Penalty(IntEnum):
	"Encodes a penalty"
	passed = 1
	doubled = 2
	redoubled = 4

	@staticmethod
	def find(name: str):
		if not name or name[0].lower() in "np" or name.lower() == "ap":
			return Penalty.passed
		if name.lower() == 'x' or name[0].lower() == 'd':
			return Penalty.doubled
		if name.lower() == 'xx' or name[0].lower() == 'r':
			return Penalty.redoubled
		raise ValueError(f"Invalid Penalty: {name}")

	@property
	def abbr(self) -> str:
		return "x" * (self >> 1)
