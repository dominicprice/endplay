__all__ = ["Rank", "AlternateRank"]

from enum import IntEnum

class Rank(IntEnum):
	"""
	Encodes the rank of a suit. The standard values use
	powers of two, however some internal functions use
	an alternative encoding AlternateRank using the 
	values 2-14.
	"""
	R2 = 0x0004
	R3 = 0x0008
	R4 = 0x0010
	R5 = 0x0020
	R6 = 0x0040
	R7 = 0x0080
	R8 = 0x0100
	R9 = 0x0200
	RT = 0x0400
	RJ = 0x0800
	RQ = 0x1000
	RK = 0x2000
	RA = 0x4000

	@property
	def abbr(self) -> str:
		return self.name[1]

	@staticmethod
	def find(value: str) -> 'Rank':
		return Rank[f"R{value.upper()}"]

	def to_alternate(self) -> 'AlternateRank':
		# Calculate integer log2
		x, y = self.value, 0
		while True:
			x >>= 1
			if x == 0:
				break
			y += 1
		return AlternateRank(y)
		
class AlternateRank(IntEnum):
	"""
	Encodes the rank of a suit using the values 2-14. Used 
	for internal functions, for APIs use the Rank class.
	"""
	R2 =  2
	R3 =  3
	R4 =  4
	R5 =  5
	R6 =  6
	R7 =  7
	R8 =  8
	R9 =  9
	RT = 10
	RJ = 11
	RQ = 12
	RK = 13
	RA = 14
	
	@property
	def abbr(self) -> str:
		return self.name[1]
		
	@staticmethod
	def find(value: str):
		return Rank[f"R{value}"]
		
	def to_standard(self) -> Rank:
		# Calculate integer power of 2
		return Rank(2 << (self.value-1))
