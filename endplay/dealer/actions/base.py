__all__ = ["BaseActions"]

from typing import Optional, Union, Callable
from abc import ABC
from endplay.types import Deal
import sys

Expr = Callable[[Deal], Union[int, float, bool]]

class BaseActions(ABC):
	def __init__(self, deals, stream):
		self.deals = deals
		self.stream = sys.stdout if stream is None else stream

	def preamble(self):
		pass

	def postamble(self):
		pass

	def printall(self):
		raise NotImplementedError

	def print(*players):
		raise NotImplementedError

	def printew():
		raise NotImplementedError

	def printpbn():
		raise NotImplementedError

	def printcompact(expr: Expr = None):
		raise NotImplementedError

	def printoneline(expr: Expr = None):
		raise NotImplementedError

	def printes(*objs: Union[Expr, str]):
		raise NotImplementedError

	def average(expr: Expr, s: Optional[str] = None):
		raise NotImplementedError

	def frequency(expr: Expr, lower_bound: float, upper_bound: float, s: Optional[str] = None):
		raise NotImplementedError

	def frequency(ex1: Expr, lb1: float, hb1: float, ex2: Expr, lb2: float, hb2: float, s: Optional[str] = None):
		raise NotImplementedError