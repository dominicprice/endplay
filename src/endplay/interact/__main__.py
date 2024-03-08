"""
An interactive interface to many of the features of endplay including
dealing hands and performing double-dummy analysis.
"""

import argparse

import endplay.config as config
from endplay.interact.commandobject import CommandObject
from endplay.interact.frontends import (
    BaseFrontend,
    CmdFrontend,
    CursesFrontend,
    HTMLFrontend,
)
from endplay.types import Denom, Player
from endplay.types.deal import Deal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-a",
        "--ascii",
        action="store_true",
        help="Turn off unicode output",
    )
    parser.add_argument(
        "-n",
        "--north",
        help="The cards in the north hand as a PBN string",
    )
    parser.add_argument(
        "-e",
        "--east",
        help="The cards in the east hand as a PBN string",
    )
    parser.add_argument(
        "-s",
        "--south",
        help="The cards in the south hand as a PBN string",
    )
    parser.add_argument(
        "-w",
        "--west",
        help="The cards in the west hand as a PBN string",
    )
    parser.add_argument(
        "-d",
        "--deal",
        help="The deal as a PBN string (note this must be quoted)",
    )
    parser.add_argument(
        "-f",
        "--first",
        help="The player initially on lead",
    )
    parser.add_argument(
        "-t",
        "--trump",
        help="The trump suit",
    )
    parser.add_argument(
        "-x",
        "--frontend",
        default="cmd",
        choices=["cmd", "curses", "html"],
        help="Which frontend engine to use, can be one of 'cmd', 'curses' or 'html'. Defaults to 'cmd'.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Make error messages more verbose (helpful for debugging).",
    )
    args = parser.parse_args()

    config.use_unicode = not args.ascii

    deal = Deal()
    if args.first:
        deal.first = Player.find(args.first)
    if args.trump:
        deal.trump = Denom.find(args.trump)
    if args.north:
        deal.north = args.north
    if args.east:
        deal.east = args.east
    if args.south:
        deal.south = args.south
    if args.west:
        deal.west = args.west

    cmdobj = CommandObject(deal)

    frontend: BaseFrontend
    if args.frontend == "cmd":
        frontend = CmdFrontend(cmdobj)
    elif args.frontend == "curses":
        frontend = CursesFrontend(cmdobj)
    elif args.frontend == "html":
        frontend = HTMLFrontend(cmdobj)
    else:
        print("Unknown frontend '{args.frontend}' specified")
        exit(1)

    frontend.interact()


if __name__ == "__main__":
    main()
