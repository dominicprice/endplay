"""
Parser for PBN files
"""

from __future__ import annotations

__all__ = ["PBNDecoder", "load", "loads", "dump", "dumps"]

import re
from enum import Enum
from io import StringIO
from itertools import chain
from typing import IO, Any, Optional, Union

from more_itertools import chunked

from endplay.config import suppress_unicode
from endplay.types import (
    Bid,
    Board,
    Card,
    Contract,
    ContractBid,
    Deal,
    Denom,
    PenaltyBid,
    Player,
    Rank,
    Vul,
)
from endplay.utils.play import (
    linearise_play,
    result_to_tricks,
    tabularise_play,
    tricks_to_result,
)


class PBNDecodeError(ValueError):
    def __init__(self, msg, line, lineno):
        super().__init__(msg)
        self.line = line
        self.lineno = lineno


class RE:
    lcomment = re.compile(r"\s*;\s*(.*?)")
    bcomment_line = re.compile(r"\s*{\s*(.*?)}")
    bcomment_begin = re.compile(r"\s*{\s*(.*)")
    bcomment_end = re.compile(r"(.*)}")
    ignore = re.compile(r"%.*")
    fileformat = re.compile(r"%\s*(EXPORT|IMPORT)", re.IGNORECASE)
    pbnversion = re.compile(r"%\s*PBN (\d+)\.(\d+)", re.IGNORECASE)
    metatag = re.compile(r"%\s*([\w-]+):\s*(.*?)")
    tagpair = re.compile(r"\[(\w+)\s+\"(.*?)\"\](\s*[;{]?.*)")
    note = re.compile(r"(\d+):(.*)")
    colname = re.compile(r"([+-]?)(\w+)(?:\\(\d+)([LR]?))?", re.IGNORECASE)


class PBNDecoder:
    metadata: dict[str, Any]
    boards: list[Board]
    prevtags: dict[str, Any]
    curtags: dict[str, Any]
    notes: dict[str, str]
    state: PBNDecoder.State
    curtag: Optional[str]
    lineno: int

    class State(Enum):
        NONE = 0
        META = 1
        DATA = 2
        COMMENTBLOCK = 3

    def __init__(self):
        # warnings.warn("endplay.parsers.PBNDecoder is now deprecated and subject to be replaced with a different interface at any time")
        self.clear()

    def _get_comment(self, text: str, iscont: bool) -> tuple[Optional[str], bool]:
        """
        Returns the comment contained in text, and a flag which
        is set to True if the comment requires continuation or
        False otherwise
        """
        if iscont:
            m = RE.bcomment_end.match(text)
            if m:
                return (m.group(1), False)
            return (text, True)
        else:
            # Match a single line comment (begins with a semicolon)
            m = RE.lcomment.match(text)
            if m:
                return (m.group(1), False)

            # Match a block comment that ends on the same line (e.g. { xyz })
            m = RE.bcomment_line.match(text)
            if m:
                return (m.group(1), False)

            # Match a block comment that begins on the line but is continued (e.g. { xy)
            m = RE.bcomment_begin.match(text)
            if m:
                return (m.group(1), True)

            # No comment found
            return (None, False)

    def _tags_to_board(self) -> Optional[Board]:
        if len(self.curtags) == 0:
            return None
        board = Board()
        declarer = None
        dealer = None
        tricks = None
        # Loop through keys, if the key has a special variable defined in the Board class,
        # then attach the value to that variable. Otherwise, add it as a tag-value(-data)
        # entry in the `info` dict
        for raw_key, fields in self.curtags.items():
            key = raw_key.lower()
            if fields["value"] == "#":
                fields = self.prevtags[raw_key]
            value = fields["value"]
            if key == "board":
                board.board_num = int(value)
            elif key == "vulnerable":
                board.vul = Vul.find(value) if value else None
            elif key == "deal":
                board.deal = Deal(value)
            elif key == "declarer":
                declarer = Player.find(value) if value else None
            elif key == "dealer":
                dealer = Player.find(value) if value else None
            elif key == "contract":
                board.contract = Contract(value or "Pass")
            elif key == "result":
                tricks = int(value or "0")
            elif key == "auction":
                # Requires converting; iterate over the bids and check for
                # special values and deal with them appropriately, otherise
                # just convert to a bid
                board.dealer = Player.find(value) if value else None
                flattened_auction = [b for row in fields["data"] for b in row]
                for bid in flattened_auction:
                    if bid.lower() == "ap":
                        # All pass, add three passes
                        for _ in range(3):
                            board.auction.append(Bid("pass"))
                    elif bid.startswith("=") and bid.endswith("="):
                        # Note; grab the reference and attach it to the previous
                        # bid's alert
                        idx = bid[1:-1]
                        board.auction[-1].alertable = True
                        board.auction[-1].announcement = self.notes.get(
                            idx, "Note not found"
                        )
                    elif bid in "-*+":
                        # either the auction has finished, or it is a unknown call. Either
                        # way, parsing the auction is finished for us.
                        break
                    else:
                        board.auction.append(Bid(bid))
            elif key == "play":
                first = Player.find(value)
                table = []
                # Convert card names to Card objects. Ignore notes (=N=), and use
                # a card with NT suit to represent an unknown/unimportant/padding card
                # Then linearise the result so that we get a flat array of cards in
                # play order
                for raw_row in fields["data"]:
                    if len(raw_row) == 1 and raw_row[0] == "*":
                        board.claimed = True
                        break
                    row: list[Card] = []
                    for card in raw_row:
                        if card.startswith("=") and card.endswith("="):
                            pass  # ignore play annotations for now
                        elif card in "+-":
                            row.append(Card(suit=Denom.nt, rank=Rank.R2))
                        elif card == "*":
                            board.claimed = True
                            row.append(Card(suit=Denom.nt, rank=Rank.R2))
                        else:
                            row.append(Card(card))
                    table.append(row)
                if board.contract is None:
                    raise RuntimeError(
                        "cannot calculate play history without a contract"
                    )
                board.play = linearise_play(table, first, board.contract.denom)
            else:
                # By default, add to the info section
                if len(fields) == 1:
                    board.info[raw_key] = value
                else:
                    board.info[raw_key] = dict(
                        headers=fields["value"], rows=fields["data"]
                    )

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
                if dealer is not None:
                    board.dealer = dealer
        return board

    def _parse_meta(self, curline: str) -> bool:
        # Match against PBN version (e.g. % PBN 2.1)
        m = RE.pbnversion.match(curline)
        if m:
            self.metadata["version"] = {
                "major": int(m.group(1)),
                "minor": int(m.group(2)),
            }
            return False
        # Match against IMPORT/EXPORT (e.g. % EXPORT)
        m = RE.fileformat.match(curline)
        if m:
            self.metadata["format"] = m.group(1).upper()
            return False
        # Match against some other metadata (e.g. % Creator: Joe Bloggs)
        m = RE.metatag.match(curline)
        if m:
            self.metadata[m.group(1)] = m.group(2)
            return False
        # Some other comment line we can ignore
        if RE.ignore.match(curline):
            return False
        # No match found, metadata section complete
        self.state = PBNDecoder.State.NONE
        return True

    def _parse_conttable(self, curline: str) -> bool:
        # Revert to PBNDecoder.State.NONE if a tag or empty line is encountered
        if RE.tagpair.match(curline) or curline == "":
            self.state = PBNDecoder.State.NONE
        # Split the line by whitespace add add the elements to the tag value
        else:
            if self.curtag is None:
                raise RuntimeError("curtag is None while parsing table")
            self.curtags[self.curtag]["data"] += [curline.split()]
        return True

    def _parse_none(self, curline: str) -> bool:
        # Empty line, start new game (or ignore if the current game is empty)
        if curline == "":
            if self.curtags:
                board = self._tags_to_board()
                if board is not None:
                    self.boards.append(board)
                    self.prevtags, self.curtags = self.curtags, {}
            return False
        # Metadata line, ignore
        if RE.ignore.match(curline):
            return False
        # Line with only a comment
        comment, needcont = self._get_comment(curline, False)
        if comment is not None:
            if needcont:
                self.state = PBNDecoder.State.COMMENTBLOCK
            return False

        # Tag pair
        m = RE.tagpair.match(curline)
        if m:
            self.curtag = m.group(1)
            # Ignore tag if repeated
            if self.curtag in self.curtags:
                return False
            # Get the comment attached to the line (if any)
            if m.group(3):
                _, needcont = self._get_comment(m.group(3), False)
                if needcont:
                    self.state = PBNDecoder.State.COMMENTBLOCK
            # Add the tag to the current game, entering into State.DATA if it is a
            # section that expects data (play, auction or *table)
            if self.curtag is None:
                raise RuntimeError("curtag is None while parsing tag")
            if self.curtag.lower() == "play" or self.curtag.lower() == "auction":
                self.curtags[self.curtag] = {"value": m.group(2), "data": []}
                self.state = PBNDecoder.State.DATA
            elif (
                self.curtag.lower().endswith("table") and self.curtag.lower() != "table"
            ):
                colnames = []
                for colname in m.group(2).split(";"):
                    cm = RE.colname.match(colname)
                    if cm:
                        if (
                            (not cm.group(1))
                            and (not cm.group(3))
                            and (not cm.group(4))
                        ):
                            colnames += [cm.group(2)]
                        else:
                            colnames += [
                                {
                                    "ordering": cm.group(1) or None,
                                    "name": cm.group(2),
                                    "minwidth": cm.group(3) or None,
                                    "alignment": cm.group(4) or None,
                                }
                            ]
                    else:
                        raise PBNDecodeError(
                            "Could not parse column name", curline, self.lineno
                        )
                self.curtags[self.curtag] = {"value": colnames, "data": []}
                self.state = PBNDecoder.State.DATA
            elif self.curtag.lower() == "note":
                # Keep a separate list of notes which will be attached to their relevant items
                idx, note = m.group(2).split(":", maxsplit=1)
                self.notes[idx] = note
            else:
                # Any other tag gets created as a tag-value pair
                self.curtags[self.curtag] = {"value": m.group(2)}
            return False
        else:
            raise PBNDecodeError("Expected a tag", curline, self.lineno)

    def _parse_commentblock(self, curline: str) -> bool:
        _, needcont = self._get_comment(curline, True)
        if not needcont:
            self.state = PBNDecoder.State.NONE
        return True

    def clear(self) -> None:
        self.metadata: dict[str, Any] = {}
        self.boards: list[Board] = []
        self.prevtags: dict[str, Any] = {}
        self.curtags: dict[str, Any] = {}
        self.notes: dict[str, str] = {}
        self.state = PBNDecoder.State.META
        self.curtag: Optional[str] = None
        self.lineno = 0

    def parse_file(self, f: IO[str]) -> list[Board]:
        "Parse a PBN file"
        self.clear()

        # Loop over lines, keeping track of what type of line we are expecting.
        # If the line isn't consumed, change the state and fallthrough to a
        # method which can consume the line. Always append a blank line to the
        # end of the file input to ensure that the last board is processed
        for curline in chain(f.readlines(), [""]):
            self.lineno += 1
            curline = curline.strip()

            if curline.startswith("%") and self.state != PBNDecoder.State.META:
                continue

            if self.state == PBNDecoder.State.META:
                if not self._parse_meta(curline):
                    continue
            if self.state == PBNDecoder.State.DATA:
                if not self._parse_conttable(curline):
                    continue
            if self.state == PBNDecoder.State.NONE:
                if not self._parse_none(curline):
                    continue
            if self.state == PBNDecoder.State.COMMENTBLOCK:
                if not self._parse_commentblock(curline):
                    continue

        return self.boards


class PBNEncoder:
    def __init__(self):
        self.tags = []
        self.pbn_version = "2.1"

    def _create_tag(
        self, key: str, value: Any, data: Optional[list[Any]] = None
    ) -> None:
        key = key[:1].upper() + key[1:]
        tagpair = f'[{key} "{value}"]'
        if data is not None:
            for line in data:
                tagpair += "\n" + " ".join(str(cell) for cell in line)
        self.tags.append(tagpair + "\n")

    def _serialize_columns(self, headers: list[Union[dict, str]]) -> str:
        colnames = []
        for col in headers:
            if isinstance(col, str):
                colname = col
            else:
                colname = ""
                if col["ordering"] is not None:
                    colname += col["ordering"]
                colname += col["name"]
                if col["minwidth"] is not None:
                    colname += "\\" + col["minwidth"]
                    if col["alignment"] is not None:
                        colname += col["alignment"]
            colnames.append(colname)
        return ";".join(colnames)

    def _justify_row(self, headers: list[dict], row: list[str]) -> list[str]:
        res = []
        for header, cell in zip(headers, row):
            if isinstance(header, str):
                minwidth = 0
                alignment = "L"
            else:
                minwidth = int(header["minwidth"] or 0)
                alignment = header["alignment"] or "L"
            if alignment == "L":
                res.append(cell.ljust(minwidth))
            else:
                res.append(cell.rjust(minwidth))
        return res

    def export_board(self, board: Board) -> None:
        # Split the board info into mandatory and supplementary tags
        event = "?"
        site = "?"
        date = "?"
        west = "?"
        north = "?"
        east = "?"
        south = "?"
        scoring = "?"
        supplementary = {}
        for raw_key, value in board.info.items():
            key = raw_key.lower()
            if key == "event":
                event = value
            elif key == "site":
                site = value
            elif key == "date":
                date = value
            elif key == "west":
                west = value
            elif key == "north":
                north = value
            elif key == "east":
                east = value
            elif key == "south":
                south = value
            elif key == "scoring":
                scoring = value
            elif key.endswith("table") and key != "table":
                headers = self._serialize_columns(value["headers"])
                rows = [
                    self._justify_row(value["headers"], row) for row in value["rows"]
                ]
                supplementary[raw_key] = Board.Info(value=headers, data=rows)
            elif isinstance(value, str):
                supplementary[raw_key] = Board.Info(value=value)
            else:
                supplementary[raw_key] = value

        with suppress_unicode():
            # Print mandatory tags
            self.tags = []
            self._create_tag("Event", event)
            self._create_tag("Site", site)
            self._create_tag("Date", date)
            self._create_tag("Board", board.board_num)
            self._create_tag("West", west)
            self._create_tag("North", north)
            self._create_tag("East", east)
            self._create_tag("South", south)
            if board.dealer is None:
                self._create_tag("Dealer", "?")
            else:
                self._create_tag("Dealer", board.dealer.abbr)
            if board.vul is None:
                self._create_tag("Vulnerable", "?")
            else:
                v = ["None", "All", "NS", "EW"][board.vul]
                self._create_tag("Vulnerable", v)
            self._create_tag("Deal", board.deal.to_pbn())
            self._create_tag("Scoring", scoring)
            if board.contract is None:
                self._create_tag("Declarer", "?")
            else:
                self._create_tag("Declarer", board.contract.declarer.abbr)
            if board.contract is None:
                self._create_tag("Contract", "?")
                self._create_tag("Result", "?")
            else:
                c = board.contract
                if c.is_passout():
                    cstr = "Pass"
                    res = ""
                else:
                    cstr = f"{c.level}{c.denom.abbr}{c.penalty.abbr}"
                    res = result_to_tricks(board.contract.result, board.contract.level)
                self._create_tag("Contract", cstr)
                self._create_tag("Result", res)

            # Print play and auction
            notes: dict[int, str] = {}
            if board.auction:
                table = []
                for row in chunked(board.auction, 4):
                    tablerow = []
                    for bid in row:
                        if isinstance(bid, ContractBid):
                            tablerow.append(f"{bid.level}{bid.denom.abbr}")
                        elif isinstance(bid, PenaltyBid):
                            tablerow.append(bid.penalty.abbr.upper() or "Pass")
                        if bid.announcement:
                            idx = len(notes) + 1
                            notes[idx] = bid.announcement
                            tablerow.append(f"={idx}=")
                    table.append(tablerow)
                if board.dealer is None:
                    raise ValueError("cannot generate Auction tag with no dealer")
                self._create_tag("Auction", board.dealer.abbr, table)

            if board.play:
                pad_value = Card(suit=Denom.nt, rank=Rank.R2)
                if board.contract is None:
                    raise ValueError("cannot generate Play tag with no contract")
                table = tabularise_play(
                    board.play, board.contract.declarer.lho, board.contract.denom
                )
                string_table = []
                for table_row in table:
                    string_row = []
                    for card in table_row:
                        if card == pad_value:
                            string_row.append("- ")
                        else:
                            string_row.append(str(card))
                    string_table.append(string_row)
                if board.claimed:
                    string_table.append(["*"])

                self._create_tag("Play", board.contract.declarer.lho.abbr, string_table)

            # Print notes
            for idx, note in notes.items():
                self._create_tag("Note", f"{idx}:{note}")

            # Print supplementary tags
            for key, value in supplementary.items():
                self._create_tag(key, value.value, value.data)

    def export_file(self, boards: list[Board], fp: IO[str]) -> None:
        "Export current data into a file object"
        fp.write(f"% PBN {self.pbn_version}\n")
        fp.write("% EXPORT\n\n")
        for board in boards:
            self.export_board(board)
            fp.writelines(self.tags)
            fp.write("\n")


def load(fp: IO[str]) -> list[Board]:
    "Read a PBN file object into a list of :class:`Board` objects"
    parser = PBNDecoder()
    return parser.parse_file(fp)


def loads(s: str) -> list[Board]:
    "Read a PBN string into a list of :class:`Board` objects"
    parser = PBNDecoder()
    sp = StringIO(s)
    return parser.parse_file(sp)


def dump(boards: list[Board], fp: IO[str]) -> None:
    "Serialize a list of :class:`Board` objects to a PBN file"
    parser = PBNEncoder()
    parser.export_file(boards, fp)


def dumps(boards: list[Board]) -> str:
    "Serialize a list of :class:`Board` objects to a PBN string"
    parser = PBNEncoder()
    sp = StringIO()
    parser.export_file(boards, sp)
    return sp.getvalue()
