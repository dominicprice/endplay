"Parser for BridgeBase LIN files"

from __future__ import annotations

__all__ = ["LINEncodeError", "dump", "dumps", "load", "loads"]

import re
from typing import IO

from more_itertools import chunked

from endplay.config import suppress_unicode
from endplay.types import (
    Bid,
    Board,
    Card,
    Contract,
    ContractBid,
    Deal,
    PenaltyBid,
    Player,
    Vul,
)
from endplay.utils.escape import escape_suits, unescape_suits
from endplay.utils.play import result_to_tricks, total_tricks, tricks_to_result


class LINDecoder:
    """
    Class providing functionality for reading the LIN file format
    """

    def __init__(self):
        pass

    def parse_line(self, line: str) -> Board:
        deal = None
        auction: list[Bid] = []
        play: list[Card] = []
        board_num = None
        dealer = None
        vul = None
        contract = None
        claimed = False
        info = {}

        elems = line.split("|")
        pairs = [(a, b) for a, b in zip(elems[::2], elems[1::2])]
        for key, value in pairs:
            if key == "st":
                # small text
                continue
            elif key == "rh":
                # reset heading
                continue
            elif key == "qx":
                # create label
                continue
            elif key == "va":
                # vertical adjust
                continue
            elif key == "sa":
                # size auction
                continue
            elif key == "mn":
                # Main name
                continue
            elif key == "bt":
                # Main name
                continue
            elif key == "tu":
                # Main name
                continue
            elif key == "nt":
                # Marks an alert for the previous bid
                auction[-1].announcement = unescape_suits(value)
            elif key == "pn":
                # Player names are comma separated starting from south
                info["South"], info["West"], info["North"], info["East"] = value.split(
                    ","
                )
            elif key == "md":
                # Marks deal, starts with dealer then comma separated hands
                dealer = Player.from_lin(int(value[0]))
                deal = Deal.from_lin(value, complete_deal=True)
            elif key == "sv":
                # Marks vulnerability
                vul = Vul.from_lin(value)
            elif key == "ah":
                # Marks board number in format 'Board N'
                board_num = int(value[5:])
            elif key == "mb":
                # Marks a bid
                auction.append(Bid(value, value[-1:] == "!"))
            elif key == "an":
                # Marks an alert for the previous bid
                auction[-1].announcement = unescape_suits(value)
            elif key == "pc":
                # Marks a card in the play section
                play.append(Card(value))
            elif key == "pg":
                # Signifies end of play
                continue
            elif key == "mc":
                # Marks that tricks were claimed
                claimed = True
                if contract is None:
                    if dealer is None:
                        raise ValueError("lin contains a contract but no dealer")
                    contract = Contract.from_auction(dealer, auction)
                    contract.result = tricks_to_result(int(value), contract.level)
            else:
                info[key] = value
        # ensure there is a contract if there was an auction
        if contract is None and (dealer is not None and len(auction) > 0):
            contract = Contract.from_auction(dealer, auction)
            if play:
                tricks = total_tricks(play, contract.denom)
                contract.result = tricks_to_result(int(tricks), contract.level)
        # make sure 'first' and 'trump' in deal are set correctly if there is
        # a contract
        if contract is not None:
            if deal is None:
                raise ValueError("lin contains contract but no deal")
            deal.first = contract.declarer.lho
            deal.trump = contract.denom
        return Board(
            deal,
            auction,
            play,
            board_num,
            vul=vul,
            dealer=dealer,
            contract=contract,
            claimed=claimed,
            **info,
        )

    def parse_string(self, lin: str) -> list[Board]:
        boards = []
        # Use regex to split on 'pn|' but keep 'pn|' in the result
        split_content = re.split(r"(pn\|)", lin)
        final_split_content = []
        for i in range(1, len(split_content), 2):
            final_split_content.append(split_content[i] + split_content[i + 1])
        for line in final_split_content:
            boards.append(self.parse_line(line))
        return boards

    def parse_file(self, f: IO[str]) -> list[Board]:
        boards = []
        # Read the file content
        content = f.read()
        # Remove CRLF characters
        cleaned_content = content.replace("\r\n", "").replace("\n", "")

        boards = self.parse_string(cleaned_content)
        return boards


class LINEncodeError(ValueError):
    pass


class LINEncoder:
    def __init__(self):
        pass

    def serialise_board(self, board: Board) -> str:
        # Early error checking
        if board.dealer is None:
            raise LINEncodeError("Cannot encode board without `dealer` set")
        if board.deal is None:
            raise LINEncodeError("Cannot encode board without `deal` set")
        with suppress_unicode():
            lin = ""
            s, w, n, e = (
                board.info.south,
                board.info.west,
                board.info.north,
                board.info.east,
            )
            lin += f"pn|{s or ''},{w or ''},{n or ''},{e or ''}|"
            lin += "st||"
            lin += f"md|{board.deal.to_lin(board.dealer)}|"
            lin += "rh||"
            if board.board_num is not None:
                lin += f"ah|Board {board.board_num}|"
            if board.vul is not None:
                lin += f"sv|{board.vul.to_lin()}|"
            for bid in board.auction:
                lin += "mb|"
                if isinstance(bid, ContractBid):
                    lin += (
                        f"{bid.level}{bid.denom.abbr[0]}"
                        + ("!" if bid.alertable else "")
                        + "|"
                    )
                elif isinstance(bid, PenaltyBid):
                    lin += bid.penalty.name[0] + ("!" if bid.alertable else "") + "|"
                if bid.announcement is not None:
                    lin += f"an|{escape_suits(bid.announcement)}|"
            lin += "pg||"
            for trick in chunked(board.play, 4):
                for card in trick:
                    lin += f"pc|{card}|"
                if len(trick) == 4:
                    lin += "pg||"
            if board.claimed:
                if board.contract is None:
                    raise ValueError("claimed board has no contract")
                tricks = result_to_tricks(board.contract.result, board.contract.level)
                lin += f"mc|{tricks}|"
        return lin


def load(fp: IO[str]) -> list[Board]:
    "Read a LIN file object into an array of :class:`Board` objects"
    parser = LINDecoder()
    return parser.parse_file(fp)


def loads(s: str) -> list[Board]:
    "Read a LIN string into a n arrya of :class:`Board` objects"
    parser = LINDecoder()
    return parser.parse_string(s)


def dump(boards: list[Board], fp: IO[str]) -> None:
    "Seralize a list of :class:`Board` objects to a LIN file"
    parser = LINEncoder()
    for board in boards:
        line = parser.serialise_board(board)
        fp.write(line + "\n")


def dumps(boards: list[Board]) -> str:
    "Serialize a list of :class:`Board` objects to a LIN string"
    parser = LINEncoder()
    lines = []
    for board in boards:
        lines.append(parser.serialise_board(board))
    return "\n".join(lines) + "\n"
