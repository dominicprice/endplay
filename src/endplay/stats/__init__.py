"""
Functions for statistical analysis of deals.
"""

from __future__ import annotations

__all__ = ["average", "frequency", "cofrequency"]

from typing import Iterable, Optional, Union
from endplay.types import Deal
from endplay.dealer.constraint import Expr
try:
	from statistics import fmean
except ImportError:
	from statistics import mean as fmean
import numpy as np
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

def average(deals: Iterable[Deal], func: Expr):
	"Return the average of a function over a sequence of deals"
	return fmean(func(deal) for deal in deals)

def histogram(
	deals: Iterable[Deal], 
	func: Expr,
	lower_bound: Optional[float] = None,
	upper_bound: Optional[float] = None,
	n_bins: Optional[int] = None) -> tuple[list[float], list[float], Figure]:
	"""
	Create a histogram from the frequency of a function over a sequence of deals
	:param deals: The input sequence of deals
	:param func: The function to apply over the deals
	:param lower_bound: The lower bound of the data to bin. Any value below this
		threshold will be placed into a single bin at the start of the histogram.
	:param upper_bound: The upper bound of the data to bin. Any value above this
		threshold will be placed in a single bin at the end of the histogram.
	:param n_bins: The number of bins to sort the data into. If not provided,
		a binning algorithm is used to estimate this value.
	"""
	# Create histogram and bins using numpy
	data = np.fromiter((func(deal) for deal in deals), float)
	if lower_bound is None:
		lower_bound = data.min()
	if upper_bound is None:
		upper_bound = data.max()
	fig, ax = plt.subplots()
	h = ax.hist(
		data, 
		bins='auto' if n_bins is None else n_bins, 
		range=(lower_bound, upper_bound),
		density=True)
	return h[0], h[1], fig

def histogram2d(
	deals: Iterable[Deal],
	funcs: tuple[Expr],
	lower_bounds: tuple[Optional[float]] = (None, None),
	upper_bounds: tuple[Optional[float]]= (None, None),
	n_bins: Union[None, int, tuple[int, int]] = None
	) -> tuple[list[list[float]], list[float], Figure]:
	"""
	Create a 2D histogram of the frequencies of two functions over a sequence
	of deals.
	:param deals: The input sequence of deals
	:param funcs: 2-element tuple containing the functions to evaluate over the deals
	:param lower_bounds: 2-element tuple containing the lower bounds of the data. Values
		which evaluate to lower than this are ignored.
	:param upper_bounds: 2-element tuple containing the upper bounds of the data. Values
		which evaluate to higher than this are ignored.
	:param n_bins: Number of bins to place the data into. If not provided, an algorithm
		guesses the optimum number of bins. Can either be a single int (same value used
		for both axes) or a 2-element tuple
	"""
	data1 = np.fromiter((funcs[0](deal) for deal in deals), float)
	data2 = np.fromiter((funcs[1](deal) for deal in deals), float)
	range1 = (
		data1.min() if lower_bounds[0] is None else lower_bounds[0],
		data1.max() if upper_bounds[0] is None else upper_bounds[0])
	range2 = (
		data2.min() if lower_bounds[1] is None else lower_bounds[1],
		data2.max() if upper_bounds[1] is None else upper_bounds[1])
	if n_bins is None:
		n_bins = 'auto'
	fig, ax = plt.subplots()
	h = ax.hist2d(data1, data2, range=(range1, range2), density=True)
	fig.colorbar(h[3])
	return h[0], h[1], fig