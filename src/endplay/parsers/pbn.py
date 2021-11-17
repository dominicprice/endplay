__all__ = ["PBNParser"]

import warnings
import re

class PBNParser:
	# Precompile some regular expressions
	re_lcomment = re.compile(r"\s*;\s*(.*)")
	re_bcomment_line = re.compile(r"\s*{\s*(.*)}")
	re_bcomment_begin = re.compile(r"\s*{\s*(.*)")
	re_bcomment_end = re.compile(r"(.*)}")
	re_ignore = re.compile(r"%.*")
	re_fileformat = re.compile(r"%\s*(EXPORT|IMPORT)", re.IGNORECASE)
	re_pbnversion = re.compile(r"%\s*PBN (\d+)\.(\d+)", re.IGNORECASE)
	re_metatag = re.compile(r"%\s*([\w-]+):\s*(.*)")
	re_tagpair = re.compile(r"\[(\w+)\s+\"(.*)\"\]")
	re_note = re.compile(r"(\d+):(.*)")
	re_colname = re.compile(r"([+-]?)(\w+)(?:\\(\d+)([LR]?))?", re.IGNORECASE)
	re_colname = re.compile(r"([+-]?)(\w+)(?:\\(\d+)([LR]?))?", re.IGNORECASE)
	
	def __init__(self):
		warnings.warn("endplay.parsers.PBNParser is now deprecated and subject to be replaced with a different interface at any time")
		self.games = []
		self.metadata = {}
		self.errorlines = []

	def _get_comment(text, iscont):
		"""
		Returns the comment contained in text, and a flag which 
		is set to True if the comment requires continuation or
		False otherwise
		"""
		if iscont:
			m = PBNFile.re_bcomment_end.match(text)
			if m:
				return (m.group(1), False)
			return (text, True)
		else:
			# Match a single line comment (begins with a semicolon)
			m = PBNFile.re_lcomment.match(text) 
			if m:
				return (m.group(1), False)
				
			# Match a block comment that ends on the same line (e.g. { xyz })
			m = PBNFile.re_bcomment_line.match(text)
			if m:
				return (m.group(1), False)
				
			# Match a block comment that begins on the line but is continued (e.g. { xy)
			m = PBNFile.re_bcomment_begin.match(text)
			if m:
				return (m.group(1), True)
		
			# No comment found
			return None
	
	def parse_file(self, f: 'TextIOWrapper') -> bool:
		"Parse a PBN file"

		# State flags
		STATE_NONE, STATE_META, STATE_CONT_LIST, STATE_CONT_TABLE, STATE_COMMENTBLOCK = 0, 1, 2, 3, 4
		
		curgame = {}
		state = STATE_META
		curtag = None
		lineno = 0
			
		for curline in f.readlines():
			lineno += 1
			curline = curline.strip()
				
			if state == STATE_META:	
				# Match against PBN version (e.g. % PBN 2.1)
				m = PBNFile.re_pbnversion.match(curline)
				if m:
					self.metadata["version"] = { "major": int(m.group(1)), "minor": int(m.group(2)) }
					continue
				# Match against IMPORT/EXPORT (e.g. % EXPORT)
				m = PBNFile.re_fileformat.match(curline)
				if m:
					self.metadata["format"] = m.group(1).upper()
					continue
				# Match against some other metadata (e.g. % Creator: Joe Bloggs)
				m = PBNFile.re_metatag.match(curline)
				if m:
					self.metadata[m.group(1)] = m.group(2)
					continue
				# Some other comment line we can ignore
				if PBNFile.re_ignore.match(curline):
					continue
				# No match found, metadata section complete
				state == STATE_NONE
					
			if state == STATE_CONT_LIST:
				# Revert to STATE_NONE if a tag or empty line is encountered
				if PBNFile.re_tagpair.match(curline) or curline == "":
					state = STATE_NONE
				# Split the line by whitespace and add the elements to the tag data
				else:
					curgame[curtag]["data"] += curline.split()
						
			if state == STATE_CONT_TABLE:
				# Revert to STATE_NONE if a tag or empty line is encountered
				if PBNFile.re_tagpair.match(curline) or curline == "":
					state = STATE_NONE
				# Split the line by whitespace add add the elements to the tag value
				else:
					curgame[curtag]["rows"] += [curline.split()]
					
			if state == STATE_NONE:
				# Empty line, start new game (or ignore if the current game is empty)
				if curline == "":
					if curgame:
						self.games.append(curgame)
						curgame = {}
					continue
				# Comment line, ignore
				if PBNFile.re_ignore.match(curline):
					continue
				# Tag pair
				m = PBNFile.re_tagpair.match(curline)
				if m:
					# Notes needs to be attached to previous tag
					if m.group(1).lower() == "note":
						cm = PBNFile.re_note.match(m.group(2))
						if cm:
							curgame[curtag]["notes"][int(cm.group(1))] = cm.group(2)
						else:
							self.errorlines.append((lineno, curline, "Could not parse note"))
					# New tag
					else:
						curtag = m.group(1)
						# Ignore tag if repeated
						if curtag in curgame:
							continue
						value = m.group(2)
						# Get the comment attached to the line (if any)
						comment = None
						if m.group(3):
							comment, needcont = _get_comment(m.group(3), False)
							if needcont:
								state = STATE_COMMENTBLOCK
						# Add the tag to the current game, entering a STATE_CONT_* if necessary
						if curtag.lower() == "play" or curtag.lower() == "auction":
							curgame[curtag] = { "value": m.group(2), "comment": comment, "notes": {}, "data": [] }
							state = STATE_CONT_LIST
						elif curtag.lower().endswith("table"):
							colnames = []
							for colname in m.group(2).split(";"):
								cm = PBNFile.re_colname.match(colname)
								if cm:
									colnames += [{
										"ordering": cm.group(1),
										"name": cm.group(2),
										"minwidth": cm.group(3),
										"alignment": cm.group(4)
									}]
								else:
									self.errorlines.append((lineno, curline, "Could not parse column name"))
									colnames += [{
										"ordering": None,
										"name": colname,
										"minwidth": None,
										"alignment": None
									}]
							curgame[curtag] = { "comment": comment, "colnames": colnames, "rows": [] }
							state = STATE_CONT_TABLE
						else:
							curgame[curtag] = { "value": m.group(2), "comment": comment, "notes": {} }
						continue
				# Unexpected line, add to errorlines
				self.errorlines.append((lineno, curline, "The line couldn't be interpreted"))
					
			if state == STATE_COMMENTBLOCK:
				comment, needcont = _get_comment(curline, True)
				curgame[curtag]["comment"] += "\n{}".format(comment)
				if not needcont:
					state == STATE_NONE
						
			
	def export(self) -> str:
		"Export current data into a string"
		raise NotImplementedError

	def export_file(self, f: 'TextIOWrapper') -> None:
		"Export current data into a file object"
		raise NotImplementedError
