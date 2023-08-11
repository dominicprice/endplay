"""
Miscellaneous input and output routines
"""

from __future__ import annotations

__all__ = ["pprint_auction"]

import sys
from collections.abc import Iterable
from typing import TextIO

from more_itertools import chunked

from endplay.types import Bid, Player


def pprint_auction(
    first: Player,
    auction: Iterable[Bid],
    *,
    include_announcements=False,
    stream: TextIO = sys.stdout,
):
    for player in first.iter_from():
        print(player.abbr.ljust(5), end="", file=stream)
    print(file=stream)
    for row in chunked(auction, 4):
        for bid in row:
            print(str(bid).ljust(5), end="", file=stream)
        print(file=stream)
    if include_announcements:
        print(file=stream)
        for bid in auction:
            if bid.announcement:
                print(f"{bid}: {bid.announcement.strip()}", file=stream)
