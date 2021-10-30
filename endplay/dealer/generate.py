__all__ = ['generate_deal', 'generate_deals']

from endplay.dealer.constraint import ConstraintInterpreter
from endplay.types import *
from random import shuffle
from typing import Union, Callable, Iterator, Optional
import warnings

def generate_deal(
	*constraints: Union[Callable, str], predeal: Deal = Deal(), 
	swapping: int = 0, max_attempts: int = 1000000, env: dict = {}) -> Deal:
	"""
	Generates a random deal satisfying the constraints, giving 13 cards to each player.
	The constraints should be supplied as functions taking a whole deal and returning
	a boolean, for example `lambda d: hcp(d.north) > 10`, or as expressions compatible 
	with the dealer expression syntax (see https://www.bridgebase.com/tools/dealer/Manual/input.html#expr)
	:param constraints: Constraints, as callables or strings
	:param max_attempts: Maximum number of shuffles to perform when finding a deal which
	                     matches the constraints. Set to -1 for infinite
	:param env: A dictionary of the environment used when evaluating constraints
	"""
	deals = generate_deals(
		*constraints, predeal=predeal, produce=1, swapping=swapping, 
		max_attempts=max_attempts, env=env)
	return next(deals)

def generate_deals(
	*constraints: Union[Callable, str], predeal: Deal = Deal(), 
	swapping: int = 0, produce: int = 40, max_attempts: int = 1000000, 
	env: dict = {}) -> Iterator[Deal]:
	"""
	Generates `produce` random deals satisfying the constraints which should
	be given as for `generate_deal`. `produce` and `max_attemps` are upper limits,
	the first to be reached terminates the program
	:param constraints: Constraints, either as callables or strings (see `generate_deal`)
	:param produce: Number of deals to produce
	:param max_attempts: Maximum number of shuffles to perform. Set to -1 for infinite
	"""
	if predeal and swapping != 0:
		warnings.warn("Use of predeal with swapping can cause unexpected results")
	if predeal is None:
		predeal = Deal()
	ci = ConstraintInterpreter()
	for name, val in env.items():
		ci.set_env(name, val)
	constraints = [ci.lambdify(c) if not callable(c) else c for c in constraints]
	cards = set(Card(suit=denom, rank=rank) for denom in Denom.suits() for rank in Rank)
	cards = list(cards.difference(predeal.to_hand()))
	split = [sum([13 - len(hand) for hand in predeal][:i]) for i in range(5)]
	res = []
	for _ in range(produce):
		produced = False
		while not produced:
			if max_attempts == 0:
				raise RuntimeError("Could not find a deal satisfying the given constraints")
			elif max_attempts > 0:
				max_attempts -= 1
			shuffle(cards)
			deal = predeal.copy()
			for i, player in enumerate(Player):
				deal[player].extend(cards[split[i]:split[i+1]])
			for perm in generate_swaps(deal, swapping):
				if all(c(perm) for c in constraints):
					yield perm
					produced = True
					break

def generate_swaps(deal: Deal, swapping: int):
	if swapping == 0:
		yield deal
	elif swapping == 2:
		yield deal
		deal.swap(0, 2)
		yield deal
	elif swapping == 3:
		for _ in range(3):
			deal.swap(1, 2)
			yield deal
			deal.swap(2, 3)
			yield deal

	else:
		raise RuntimeError(f"Invalid swapping value {swapping} used")
