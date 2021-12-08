"""
A shell-like CLI interface to many of the features of endplay including 
dealing hands and performing double-dummy analysis.
"""

import endplay.config as config
from endplay.types import Player, Denom
from endplay.interact.interactivedeal import InteractiveDeal
from endplay.interact.frontends import CmdFrontend, CursesFrontend, TkFrontend
import argparse

def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("-a", "--ascii", action='store_true', help="Turn off unicode output")
	parser.add_argument("-n", "--north", help="The cards in the north hand as a PBN string")
	parser.add_argument("-e", "--east", help="The cards in the east hand as a PBN string")
	parser.add_argument("-s", "--south", help="The cards in the south hand as a PBN string")
	parser.add_argument("-w", "--west", help="The cards in the west hand as a PBN string")
	parser.add_argument("-d", "--deal", help="The deal as a PBN string (note this must be quoted)")
	parser.add_argument("-f", "--first", help="The player initially on lead")
	parser.add_argument("-t", "--trump", help="The trump suit")
	parser.add_argument("-x", "--frontend", default='cmd', choices=["cmd", "curses", "tk"], help="Which frontend engine to use, can be one of 'cmd', 'curses' or 'tk'. Defaults to 'cmd'.")
	parser.add_argument("-v", "--verbose", action="store_true", help="Make error messages more verbose (helpful for debugging).")
	args = parser.parse_args()

	config.use_unicode = not args.ascii

	d = InteractiveDeal(args.deal)
	if args.first: d.first = Player.find(args.first)
	if args.trump: d.trump = Denom.find(args.trump)
	if args.north: d.north = args.north
	if args.east: d.east = args.east
	if args.south: d.south = args.south
	if args.west: d.west = args.west

	if args.frontend == "cmd":
		frontend = CmdFrontend(d, verbose_errors=args.verbose)
	elif args.frontend == "curses":
		frontend = CursesFrontend(d)
	elif args.frontend == "tk":
		frontend = TkFrontend(d)
	else:
		print("Unknown frontend '{args.frontend}' specified")
		exit(1)

	frontend.interact()

if __name__ == "__main__":
	main()