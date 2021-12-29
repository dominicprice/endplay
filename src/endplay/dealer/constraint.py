"""
Engine for converting dealer-syntax expressions into evaluatable
Python functions. You should not need to use this directly unless
you are developing your own functions, as most functions accept
strings as well as functions and automatically compile them using
the machinery in this module.
"""

__all__ = [ "ConstraintInterpreter" ]

import re
from typing import Callable, Any, Union
from endplay.parsers.dealer import Node, DealerParser
from endplay.types import Deal, Denom, Rank
from endplay.evaluate import (hcp, standard_hcp_scale, losers, controls, cccc, quality, exact_shape)
from endplay.dds import analyse_play

Expr = Callable[[Deal], Union[float, int, bool]]

class ConstraintInterpreter:
	"""
	Provides an interface for evaluating constraints in the Dealer program syntax
	and testing them against a deal
	"""

	# Precompiled regexes for matching some more complex function names
	_re_suit = re.compile(r"(?:spades?)|(?:hearts?)|(?:diamonds?)|(?:clubs)")
	_re_pt = re.compile(r"(?:pt[0-9])")
	_re_namedpt = re.compile(r"(?:tens?)|(?:jacks?)|(?:queens?)|(?:kings?)|(?:aces?)|(?:top[2-5])|(?:c13)")

	def __init__(self):
		self.parser = DealerParser()
		self.reset_env()

	def set_env(self, name: str, value: Any):
		"""
		Insert a new variable into the interpreter's environment or change the value 
		of an existing variable

		:param name: The name of the environment variable
		:param value: The new value of the variable
		"""
		self._env[name] = value

	def unset_env(self, name: str):
		"""
		Remove an variable from the interpreter's environment. Attempting to remove an
		essential variable (one of the ptN scale definitions) throws an error

		:param name: The name of the variable to remove
		"""
		if _re_pt.match(name):
			raise RuntimeError(f"Trying to unset required environment variable {name}")
		del self._env[name]

	def get_env(self, name: str) -> Any:
		":return: The value of the named environment variable"
		return self._env[name]


	def reset_env(self):
		"Reinitialise the environment to the default values"
		self._env = {
			"pt0": [0,0,0,0,1,0,0,0,0,0,0,0,0], 
			"pt1": [0,0,0,1,0,0,0,0,0,0,0,0,0], 
			"pt2": [0,0,1,0,0,0,0,0,0,0,0,0,0],
			"pt3": [0,1,0,0,0,0,0,0,0,0,0,0,0], 
			"pt4": [1,0,0,0,0,0,0,0,0,0,0,0,0], 
			"pt5": [1,1,0,0,0,0,0,0,0,0,0,0,0],
			"pt6": [1,1,1,0,0,0,0,0,0,0,0,0,0], 
			"pt7": [1,1,1,1,0,0,0,0,0,0,0,0,0], 
			"pt8": [1,1,1,1,1,0,0,0,0,0,0,0,0],
			"pt9": [6,4,2,1,0,0,0,0,0,0,0,0,0]
		}

	def parse(self, s: str) -> Node:
		"Parse an expression string into a syntax tree"
		return self.parser.parse_expr(s)

	def evaluate(self, node: Union[Node, str], deal: Deal) -> float:
		"Evaluate an expression tree over a specific deal into a logical or arithmetic type"
		if isinstance(node, str):
			node = self.parse(node)
		if node.dtype == Node.ROOT:
			# root node is just dummy, keep going down the tree
			return self.evaluate(node.last_child)
		elif node.dtype == Node.SYMBOL:
			# symbols evaluate to their value in the environment and
			# are evaluated if they are Node instances
			val = self._env[node.value]
			if isinstance(val, Node):
				return self.evaluate(val, deal)
			else:
				return val
		elif node.dtype == Node.VALUE:
			# values evaluate to themselves
			return node.value
		elif node.dtype == Node.FUNCTION:
			# functions get dispatched
			return self._dispatch_function(node, deal)
		elif node.dtype == Node.OPERATOR:
			# operators get dispatched
			return self._dispatch_operator(node, deal)
		else:
			raise RuntimeError(f"Constraint contains unexpected node type {node.dtype}")

	def lambdify(self, node: Union[Node, str]) -> Expr:
		"""
		Convert an expression tree (or string) into an anonymous function accepting a single
		:class:`Deal` argument and returning the expression evaluated over this deal

		:param node: The root of the expression tree, or a string containing an expression
		"""
		if isinstance(node, str):
			node = self.parse(node)
		return lambda deal: self.evaluate(node, deal)

	def _evaluate_shape(self, node, shape):
		if node.dtype == Node.OPERATOR:
			if node.value == "any":
				tshape = shape.copy()
				pred = [x for x in node.first_child.value if x != None]
				n_wildcards = len(node.first_child.value) - len(pred)
				try:
					for elem in pred:
						tshape.remove(elem)
				except ValueError:
					return False
				return n_wildcards == len(tshape)
			else:
				lhs = self._evaluate_shape(node.first_child, shape)
				rhs = self._evaluate_shape(node.last_child, shape)
				if node.value == "+":
					return lhs or rhs
				else:
					return lhs and (not rhs)
				return rhs if node.value == "+" else (not rhs)
		elif node.dtype == Node.VALUE:
			for a, b in zip(shape, node.value):
				if b is not None and a != b:
					return False
			return True
		else:
			raise RuntimeError(f"Unexpected node type {node.dtype} in shape expression")


	def _dispatch_function(self, node, deal):
		if node.value == "hcp":
			return self._fn_hcp(node, deal, standard_hcp_scale)
		elif ConstraintInterpreter._re_suit.match(node.value):
			return self._fn_suit(node, deal)
		elif ConstraintInterpreter._re_pt.match(node.value):
			return self._fn_hcp(node, deal, self._env[node.value])
		elif ConstraintInterpreter._re_namedpt.match(node.value):
			if node.value == 'c13':
				idx = 9
			elif node.value[:-1] == 'top':
				idx = 3 + int(node.value[-1])
			else:
				idx = "tjqka".find(node.value[0])
			return self._fn_hcp(node, deal, self._env[f"pt{idx}"])
		elif node.value == "shape":
			return self._fn_shape(node, deal)
		elif node.value == "control" or node.value == "controls":
			return self._fn_control(node, deal)
		elif node.value == "loser" or node.value == "losers":
			return self._fn_loser(node, deal)
		elif node.value == "cccc":
			return self._fn_cccc(node, deal)
		elif node.value == "quality":
			return self._fn_quality(node, deal)
		elif node.value == "trick" or node.value == "tricks":
			return self._fn_trick(node, deal)
		elif node.value == "score":
			return self._fn_score(node, deal)
		elif node.value == "hascard":
			return self._fn_hascard(node, deal)
		elif node.value == "imp" or node.value == "imps":
			return self._fn_imp(node, deal)
		else:
			raise ValueError(f"Unknown function {node.value}")

	def _fn_hascard(self, node, deal):
		player = node.first_child.value
		card = node.last_child.value
		return card in deal[player]

	def _fn_hcp(self, node, deal, scale):
		if node.n_children == 1:
			return hcp(deal[node.first_child.value], scale)
		elif node.n_children == 2:
			return hcp(deal[node.first_child.value][node.last_child.value], scale)
		else:
			raise RuntimeError(f"hcp() given {node.n_children} arguments, expected 2")

	def _fn_suit(self, node, deal):
		suit = Denom.find(node.value)
		player = node.first_child.value
		return len(deal[player][suit])

	def _fn_control(self, node, deal):
		if node.n_children == 1:
			return controls(deal[node.first_child.value])
		elif node.n_children == 2:
			return controls(deal[node.first_child.value][node.last_child.value])
		else:
			raise RuntimeError(f"controls() given {node.n_children} arguments, expected 2")

	def _fn_loser(self, node, deal):
		if node.n_children == 1:
			return losers(deal[node.first_child.value])
		elif node.n_children == 2:
			return losers(deal[node.first_child.value][node.last_child.value])
		else:
			raise RuntimeError(f"loser() given {node.n_children} arguments, expected 2")

	def _fn_cccc(self, node, deal):
		hand = deal[node.first_child.value]
		return cccc(hand)
	
	def _fn_quality(self, node, deal):
		suit = deal[node.first_child.value][node.last_child.value]
		return quality(suit)

	def _fn_trick(self, node, deal):
		pos = node.first_child.value
		strain = node.last_child.value
		deal.first = pos.lho
		deal.trump = strain
		r = analyse_play(deal, [])
		return r[0]

	def _fn_score(self, node, deal):
		vul = node.first_child.value
		contract = node.middle_child.value
		result = node.last_child.value
		contract.result = result
		return contract.score(vul)

	def _fn_imps(self, node, deal):
		raise NotImplementedError

	def _fn_shape(self, node, deal):
		hand = deal[node.first_child.value]
		s = exact_shape(hand)
		return self._evaluate_shape(node.last_child, s)


	def _fn_hascard(self, node, deal):
		hand = deal[node.first_child.value]
		return node.last_child.value in hand

	def _fn_if(self, node, deal):
		if self.evaluate(node.first_child):
			return self.evaluate(node.middle_child, deal)
		else:
			return self.evaluate(node.last_child, deal)

	def _dispatch_operator(self, node, deal):
		if node.value in ["&&", "and"]:
			return self._op_and(node, deal)
		elif node.value in ["||", "or"]:
			return self._op_or(node, deal)
		elif node.value in ["!", "not"]:
			return self._op_not(node, deal)
		elif node.value == "==":
			return self._op_equal(node, deal)
		elif node.value == "!=":
			return self._op_notequal(node, deal)
		elif node.value == "<":
			return self._op_less(node, deal)
		elif node.value == "<=":
			return self._op_leq(node, deal)
		elif node.value == ">":
			return self._op_greater(node, deal)
		elif node.value == ">=":
			return self._op_geq(node, deal)
		elif node.value == "+":
			return self._op_add(node, deal)
		elif node.value == "-":
			return self._op_sub(node, deal)
		elif node.value == "*":
			return self._op_mul(node, deal)
		elif node.value == "/":
			return self._op_div(node, deal)
		elif node.value == "%":
			return self._op_mod(node, deal)
		else:
			raise ValueError(f"Unknown operator {node.value}")

	def _op_and(self, node, deal):
		return self.evaluate(node.first_child, deal) and self.evaluate(node.last_child, deal)
		
	def _op_or(self, node, deal):
		return self.evaluate(node.first_child, deal) or self.evaluate(node.last_child, deal)

	def _op_not(self, node, deal):
		return not self.evaluate(node.first_child, deal)

	def _op_equal(self, node, deal):
		return self.evaluate(node.first_child, deal) == self.evaluate(node.last_child, deal)

	def _op_notequal(self, node, deal):
		return self.evaluate(node.first_child, deal) != self.evaluate(node.last_child, deal)

	def _op_less(self, node, deal):
		return self.evaluate(node.first_child, deal) < self.evaluate(node.last_child, deal)

	def _op_leq(self, node, deal):
		return self.evaluate(node.first_child, deal) <= self.evaluate(node.last_child, deal)

	def _op_greater(self, node, deal):
		return self.evaluate(node.first_child, deal) > self.evaluate(node.last_child, deal)
	
	def _op_geq(self, node, deal):
		return self.evaluate(node.first_child, deal) >= self.evaluate(node.last_child, deal)

	def _op_add(self, node, deal):
		return self.evaluate(node.first_child, deal) + self.evaluate(node.last_child, deal)

	def _op_sub(self, node, deal):
		return self.evaluate(node.first_child, deal) - self.evaluate(node.last_child, deal)

	def _op_mul(self, node, deal):
		return self.evaluate(node.first_child, deal) * self.evaluate(node.last_child, deal)

	def _op_div(self, node, deal):
		return self.evaluate(node.first_child, deal) / self.evaluate(node.last_child, deal)

	def _op_mod(self, node, deal):
		return self.evaluate(node.first_child, deal) % self.evaluate(node.last_child, deal)
