"""
Functions for statistical analysis of deals.
"""

from __future__ import annotations

__all__ = ["average", "frequency", "cofrequency"]

from typing import Optional
from collections.abc import Iterable
from endplay.types import Deal
from endplay.dealer.constraint import Expr
from math import floor, ceil
try:
	from statistics import fmean
except ImportError:
	from statistics import mean as fmean


def average(deals: Iterable[Deal], func: Expr):
	"Return the average of a function over a sequence of deals"
	return fmean(func(deal) for deal in deals)

def frequency(deals: Iterable[Deal], func: Expr, lb: int, ub: int) -> list[int]:
	"""
	Calculate the value of a function over a range of deals, and bin the results into
	unit-sized bins around integer values from `lb` to `ub`
	
	:param deals: The input sequence of deals
	:param func: The function to evaluate over `deals`
	:param lb: Value below which values are ignored
	:param ub: Value above which values are ignored
	:return: An array of bins, and a tuple containing the left and right boundaries
	"""
	lb, ub = floor(lb), ceil(ub)
	bins = list(range(lb, ub+1))
	hist = [0] * len(bins)
	for deal in deals:
		val = round(func(deal))
		if bins[0] <= val <= bins[-1]:
			hist[val - bins[0]] += 1
	return hist

def cofrequency(
	deals: Iterable[Deal],
	func1: Expr,
	func2: Expr,
	lb1: Optional[float] = None,
	ub1: Optional[float] = None,
	lb2: Optional[float] = None,
	ub2: Optional[float] = None) -> list[list[int]]:
	"""
	Calculate the value of two functions over a range of deals, and bin the results into
	unit-sized bins around integer values from `lb` to `ub` to form a matrix

	:param deals: The input sequence of deals
	:param func1: The first function to evaluate over `deals`
	:param func2: The second function to evaluate over `deals`
	:param lower_bound1: Value below which values returned from func1 are ignored
	:param upper_bound1: Value above which values returned from func1 are ignored
	:param lower_bound2: Value below which values returned from func2 are ignored
	:param upper_bound2: Value above which values returned from func2 are ignored
	"""
	lb1, ub1 = floor(lb1), ceil(ub1)
	lb2, ub2 = floor(lb2), ceil(ub2)
	data1, data2 = [], []
	for deal in deals:
		data1.append(round(func1(deal)))
		data2.append(round(func2(deal)))
	bins1 = list(range(lb1, ub1+1))
	bins2 = list(range(lb2, ub2+1))
	hist = [[0 for _ in bins2] for _ in bins1]
	for val1 in data1:
		if not (lb1 <= val1 <= ub1):
			continue
		for val2 in data2:
			if not (lb2 <= val2 <= ub2):
				continue
			hist[val1 - bins1[0]][val2 - bins2[0]] += 1
	return hist