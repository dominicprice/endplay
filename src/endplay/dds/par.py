__all__ = ["par"]

from typing import Union, Optional
import endplay._dds as _dds
from endplay.types import Deal, DDTable, ParList, Vul, Player
from endplay.dds.ddtable import calc_dd_table

def par(
	deal: Union[Deal, DDTable], 
	vul: Union[Vul, int], 
	dealer: Player) -> ParList:
	"""
	Calculate the par contract result for the given deal. 

	:param deal: The deal to calculate the par result of. If you have already precomputed a DDTable for
		a deal then you speed up the par calculation by passing that instead of the Deal object
	:param vul: The vulnerability of the deal. If you pass an `int` then this is converted from a board
		number into the vulnerability of that board
	:param dealer: The dealer of the board.
	"""
	if isinstance(deal, Deal):
		dd_table = calc_dd_table(deal)
	else:
		dd_table = deal
	if not isinstance(vul, Vul):
		vul = Vul.from_board(vul)

	par = _dds.parResultsMaster()
	_dds.DealerParBin(dd_table._data, par, dealer, vul)
	return ParList(par)

