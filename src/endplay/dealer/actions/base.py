"""
Base actions class to provide the interface.
"""

__all__ = ["BaseActions"]

import sys
import os
from importlib.resources import read_text
from typing import Optional, Union
from abc import ABC, abstractmethod
from endplay.types import Deal, Player
from endplay.dealer.constraint import Expr

class BaseActions(ABC):
	def __init__(self, deals, stream, board_numbers, template_ext=None):
		self.board_numbers = board_numbers
		self.deals = deals
		self.stream = sys.stdout if stream is None else stream
		self.write = lambda *objs, **kwargs: print(*objs, **kwargs, file=self.stream)
		if template_ext is not None:
			self.preamble = read_text("endplay.dealer.actions.templates", "preamble." + template_ext)
			self.postamble = read_text("endplay.dealer.actions.templates", "postamble." + template_ext)
		else:
			self.preamble = self.postamble = ""

	def write(self, *objs, **kwargs):
		if "file" in kwargs:
			raise RuntimeError("Unexpected keyword argument 'file' passed to BaseActions.write")
		print(*objs, **kwargs, file=self.stream)

	def write_preamble(self):
		self.write(self.preamble)

	def write_postamble(self):
		self.write(self.postamble)

	def printall(self):
		self.print(*Player)

	@abstractmethod
	def print(self, *players):
		raise NotImplementedError

	def printew(self):
		self.print(Player.east, Player.west)

	@abstractmethod
	def printpbn(self):
		pass

	@abstractmethod
	def printcompact(self, expr: Expr = None):
		pass

	@abstractmethod
	def printoneline(self, expr: Expr = None):
		pass

	@abstractmethod
	def printes(self, *objs: Union[Expr, str]):
		pass

	@abstractmethod
	def average(self, expr: Expr, s: Optional[str] = None):
		pass

	@abstractmethod
	def frequency1d(
		self, expr: Expr, lower_bound: float, upper_bound: float, 
		s: Optional[str] = None):
		pass

	@abstractmethod
	def frequency2d(
		self, ex1: Expr, lb1: float, hb1: float, ex2: Expr, 
		lb2: float, hb2: float, s: Optional[str] = None):
		pass