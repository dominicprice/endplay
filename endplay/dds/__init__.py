"""
Higher-level wrappers around Bo Haglund's dds wrapper, using the
Python types defined in `endplay.types` and which use sensible
defaults for the internal state such as threading indexes.
"""

__all__ = [
	'init', 'solve_board', 'solve_all_boards', 'calc_dd_table',
	'calc_all_tables', 'analyse_play', 'analyse_all_plays', 'par'
]


import endplay._dds as _dds
from endplay.dds.solve import solve_board, solve_all_boards
from endplay.dds.ddtable import calc_dd_table, calc_all_tables
from endplay.dds.analyse import analyse_play, analyse_all_plays
from endplay.dds.par import par

init = _dds.init
