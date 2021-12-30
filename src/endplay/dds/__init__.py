"""
Higher-level wrappers around Bo Haglund's dds wrapper, using the
Python types defined in `endplay.types` and which use sensible
defaults for the internal state such as threading indexes.
"""

__all__ = [
	'solve_board', 'solve_all_boards', 'calc_dd_table',
	'calc_all_tables', 'analyse_play', 'analyse_all_plays', 'par',
	'analyse_start', 'analyse_all_starts'
]

import endplay._dds as _dds
from endplay.dds.solve import solve_board, solve_all_boards
from endplay.dds.ddtable import calc_dd_table, calc_all_tables
from endplay.dds.analyse import analyse_play, analyse_all_plays, analyse_start, analyse_all_starts
from endplay.dds.parscore import par
