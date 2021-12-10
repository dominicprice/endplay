"""
Parser for PBN files
"""

from __future__ import annotations

__all__ = ["PBNParser"]

import warnings
import re
from endplay.types import Deal, Denom, Rank, Bid, Vul, Card, Player, Board, Contract
from endplay.utils import linearise_play, tricks_to_result
from typing import TextIO

class PBNParser:
	# Precompile some regular expressions
	re_lcomment = re.compile(r"\s*;\s*(.*?)")
	re_bcomment_line = re.compile(r"\s*{\s*(.*?)}")
	re_bcomment_begin = re.compile(r"\s*{\s*(.*)")
	re_bcomment_end = re.compile(r"(.*)}")
	re_ignore = re.compile(r"%.*")
	re_fileformat = re.compile(r"%\s*(EXPORT|IMPORT)", re.IGNORECASE)
	re_pbnversion = re.compile(r"%\s*PBN (\d+)\.(\d+)", re.IGNORECASE)
	re_metatag = re.compile(r"%\s*([\w-]+):\s*(.*?)")
	re_tagpair = re.compile(r"\[(\w+)\s+\"(.*?)\"\](\s*[;{]?.*)")
	re_note = re.compile(r"(\d+):(.*)")
	re_colname = re.compile(r"([+-]?)(\w+)(?:\\(\d+)([LR]?))?", re.IGNORECASE)
	re_colname = re.compile(r"([+-]?)(\w+)(?:\\(\d+)([LR]?))?", re.IGNORECASE)
	
	def __init__(self):
		warnings.warn("endplay.parsers.PBNParser is now deprecated and subject to be replaced with a different interface at any time")
		self.metadata = {}
		self.errorlines = []

	def _get_comment(text, iscont: bool):
		"""
		Returns the comment contained in text, and a flag which 
		is set to True if the comment requires continuation or
		False otherwise
		"""
		if iscont:
			m = PBNParser.re_bcomment_end.match(text)
			if m:
				return (m.group(1), False)
			return (text, True)
		else:
			# Match a single line comment (begins with a semicolon)
			m = PBNParser.re_lcomment.match(text) 
			if m:
				return (m.group(1), False)
				
			# Match a block comment that ends on the same line (e.g. { xyz })
			m = PBNParser.re_bcomment_line.match(text)
			if m:
				return (m.group(1), False)
				
			# Match a block comment that begins on the line but is continued (e.g. { xy)
			m = PBNParser.re_bcomment_begin.match(text)
			if m:
				return (m.group(1), True)
		
			# No comment found
			return None

	def _create_board(self, tags):
		board = Board()
		declarer = None
		tricks = None
		board.info["players"] = {}
		for key, fields in tags.items():
			key = key.lower()
			value = fields["value"]
			if key == "board":
				board.board_num = int(value)
			elif key == "west":
				board.info["players"][Player.west] = value
			elif key == "north":
				board.info["players"][Player.north] = value
			elif key == "east":
				board.info["players"][Player.east] = value
			elif key == "south":
				board.info["players"][Player.south] = value
			elif key == "vulnerable":
				board.vul = Vul.find(value)
			elif key == "deal":
				board.deal = Deal(value)
			elif key == "declarer":
				declarer = Player.find(value)
			elif key == "contract":
				board.contract = Contract(value)
			elif key == "result":
				tricks = int(value)
			elif key == "auction":
				board.dealer = Player.find(value)
				for bid in fields["data"]:
					if bid.lower == "ap":
						for _ in range(3):
							board.auction.append(Bid("pass"))
					elif bid.startswith("=") and bid.endswith("="):
						board.auction[-1].alert = bid[1:-1]
					elif bid == "-":
						break
					else:
						board.auction.append(Bid(bid))
			elif key == "play":
				first = Player.find(value)
				for card in fields["data"]:
					if card.startswith("=") and card.endswith("="):
						pass # ignore play annotations for now
					elif card in "+-":
						board.play.append(Card(suit=Denom.nt, rank=Rank.R2))
					elif card == "*":
						break
					else:
						board.play.append(Card(card))
				board.play = linearise_play(fields["data"], first)
			elif key == "note":
				# try and find the corresponding bid
				index, note = value.split(":", maxsplit=1)
				for bid in board.auction:
					if bid.alert is not None and bid.alert == index:
						bid.alert = note
						break
			else:
				# By default, add to the info section
				if len(fields) == 1:
					board.info[key] = value
				else:
					board.info[key] = fields

		# housekeeping: if declarer/result are manually specified
		# then add to the contract
		if board.contract is not None:
			if declarer is not None:
				board.contract.declarer = declarer
			if tricks is not None:
				board.contract.result = tricks_to_result(tricks, board.contract.level)
			# set first and trump on deal
			if board.deal is not None:
				board.deal.first = board.contract.declarer.lho
				board.deal.trump = board.contract.denom
		return board
	
	def parse_file(self, f: TextIO) -> list[Board]:
		"Parse a PBN file"

		# State flags
		STATE_NONE, STATE_META, STATE_CONT_LIST, STATE_CONT_TABLE, STATE_COMMENTBLOCK = 0, 1, 2, 3, 4
		
		boards = []
		curtags = {}
		state = STATE_META
		curtag = None
		lineno = 0
			
		for curline in f.readlines():
			lineno += 1
			curline = curline.strip()
				
			if state == STATE_META:	
				# Match against PBN version (e.g. % PBN 2.1)
				m = PBNParser.re_pbnversion.match(curline)
				if m:
					self.metadata["version"] = { "major": int(m.group(1)), "minor": int(m.group(2)) }
					continue
				# Match against IMPORT/EXPORT (e.g. % EXPORT)
				m = PBNParser.re_fileformat.match(curline)
				if m:
					self.metadata["format"] = m.group(1).upper()
					continue
				# Match against some other metadata (e.g. % Creator: Joe Bloggs)
				m = PBNParser.re_metatag.match(curline)
				if m:
					self.metadata[m.group(1)] = m.group(2)
					continue
				# Some other comment line we can ignore
				if PBNParser.re_ignore.match(curline):
					continue
				# No match found, metadata section complete
				state = STATE_NONE
					
			if state == STATE_CONT_LIST:
				# Revert to STATE_NONE if a tag or empty line is encountered
				if PBNParser.re_tagpair.match(curline) or curline == "":
					state = STATE_NONE
				# Split the line by whitespace and add the elements to the tag data
				else:
					curtags[curtag]["data"] += curline.split()
						
			if state == STATE_CONT_TABLE:
				# Revert to STATE_NONE if a tag or empty line is encountered
				if PBNParser.re_tagpair.match(curline) or curline == "":
					state = STATE_NONE
				# Split the line by whitespace add add the elements to the tag value
				else:
					curtags[curtag]["data"] += [curline.split()]
					
			if state == STATE_NONE:
				# Empty line, start new game (or ignore if the current game is empty)
				if curline == "":
					if curtags:
						board = self._create_board(curtags)
						boards.append(board)
						curtags = {}
					continue
				# Comment line, ignore
				if PBNParser.re_ignore.match(curline):
					continue
				# Tag pair
				m = PBNParser.re_tagpair.match(curline)
				if m:
					# Notes needs to be attached to previous tag
					if m.group(1).lower() == "note":
						cm = PBNParser.re_note.match(m.group(2))
						if cm:
							curtags[curtag]["notes"][int(cm.group(1))] = cm.group(2)
						else:
							self.errorlines.append((lineno, curline, "Could not parse note"))
					# New tag
					else:
						curtag = m.group(1)
						# Ignore tag if repeated
						if curtag in curtags:
							continue
						value = m.group(2)
						# Get the comment attached to the line (if any)
						comment = None
						if m.group(3):
							comment, needcont = PBNParser._get_comment(m.group(3), False)
							if needcont:
								state = STATE_COMMENTBLOCK
						# Add the tag to the current game, entering a STATE_CONT_* if necessary
						if curtag.lower() == "play" or curtag.lower() == "auction":
							curtags[curtag] = { "value": m.group(2), "comment": comment, "notes": {}, "data": [] }
							state = STATE_CONT_LIST
						elif curtag.lower().endswith("table"):
							colnames = []
							for colname in m.group(2).split(";"):
								cm = PBNParser.re_colname.match(colname)
								if cm:
									colnames += [{
										"ordering": cm.group(1) or None,
										"name": cm.group(2),
										"minwidth": cm.group(3) or None,
										"alignment": cm.group(4) or None
									}]
								else:
									self.errorlines.append((lineno, curline, "Could not parse column name"))
									colnames += [{
										"ordering": None,
										"name": colname,
										"minwidth": None,
										"alignment": None
									}]
							curtags[curtag] = { "comment": comment, "value": colnames, "data": [] }
							state = STATE_CONT_TABLE
						else:
							curtags[curtag] = { "value": m.group(2), "comment": comment, "notes": {} }
						continue
				# Unexpected line, add to errorlines
				self.errorlines.append((lineno, curline, "The line couldn't be interpreted"))
					
			if state == STATE_COMMENTBLOCK:
				comment, needcont = PBNParser._get_comment(curline, True)
				curtags[curtag]["comment"] += "\n{}".format(comment)
				if not needcont:
					state == STATE_NONE
		return boards				
			
	def export(self) -> str:
		"Export current data into a string"
		raise NotImplementedError

	def export_file(self, f: TextIO) -> None:
		"Export current data into a file object"
		raise NotImplementedError

if __name__ == "__main__":
	pp = PBNParser()
	with open("/home/dominic/Desktop/AlsReg6-Final.pbn") as f:
		data = pp.parse_file(f)
