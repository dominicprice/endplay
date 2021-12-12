"""
Functions for escaping suit symbols
"""

from __future__ import annotations

__all__ = ["escape_suits", "unescape_suits"]

import re

_escape_suits_table = str.maketrans({
	"♠": "!S",
	"♥": "!H",
	"♦": "!D",
	"♣": "!C"
})

def escape_suits(s: str):
	"""
	Escape unicode suit symbols into BBO suit notation (!S, !H, !D, !C)
	"""
	return s.translate(_escape_suits_table)

def unescape_suits(s: str):
	"""
	Unescape BBO suit notation (!S, !H, !D, !C) into unicode suit symbols
	"""
	s = re.sub("!s", "♠", s, flags=re.IGNORECASE)
	s = re.sub("!h", "♥", s, flags=re.IGNORECASE)
	s = re.sub("!d", "♦", s, flags=re.IGNORECASE)
	return re.sub("!c", "♣", s, flags=re.IGNORECASE)
