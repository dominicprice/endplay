__all__ = ["calc_dd_table", "calc_all_tables"]

from typing import Iterable
import endplay._dds as _dds
from endplay.types import Deal, DDTable, DDTableList, Denom

def calc_dd_table(deal: Deal) -> DDTable:
	"""
	Calculates the double dummy results for all 20 possible combinations of
	dealer and trump suit for a given deal
	"""
	# Convert deal into ddTableDeal
	dl = _dds.ddTableDeal()
	dl.cards = deal._data.remainCards

	table =_dds.ddTableResults()
	_dds.CalcDDtable(dl, table)
	return DDTable(table)

def calc_all_tables(deals: Iterable[Deal], exclude: Iterable[Denom] = []) -> DDTableList:
	"""
	Optimized version of calc_dd_table for multiple deals which uses threading to
	speed up the calculation. `exclude` can contain a list of denominations to
	exclude from the calculation, e.g. if only the notrump results for the deals
	is required then pass `Denom.suits()` 
	"""
	# Convert deals to ddTableDeals
	dealsp = _dds.ddTableDeals()
	dealsp.noOfTables = 0
	for i, deal in enumerate(deals):
		if i > _dds.MAXNOOFTABLES * 5:
			raise RuntimeError(f"Too many boards, maximum is {_dds.MAXNOOFTABLES * 5}")
		dealsp.ddTableDeal[i].cards = deal._data.remainCards
		dealsp.noOfTables += 1

	# Convert exclude to a trump filter list
	trumpFilter = [False]*5
	for trump in exclude:
		trumpFilter[trump] = True

	resp = _dds.ddTablesRes()
	presp = _dds.allParResults()
	_dds.CalcAllTables(dealsp, -1, trumpFilter, resp, presp)
	resp.noOfBoards = dealsp.noOfTables
	return DDTableList(resp)