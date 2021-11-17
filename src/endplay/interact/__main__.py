"""
A shell-like CLI interface to many of the features of endplay including 
dealing hands and performing double-dummy analysis.
"""

from endplay.interact import interact
from endplay.types import Deal, Player, Denom
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
	args = parser.parse_args()

	d = Deal(args.deal)
	if args.first: d.first = Player.find(args.first)
	if args.trump: d.trump = Denom.find(args.trump)
	if args.north: d.north = args.north
	if args.east: d.east = args.east
	if args.south: d.south = args.south
	if args.west: d.west = args.west

	interact(d)

if __name__ == "__main__":
	main()