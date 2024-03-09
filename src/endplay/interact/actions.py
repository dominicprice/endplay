"""
The actions which can be applied to a `CommandObject`.
"""

from abc import ABC, abstractmethod, abstractproperty
from typing import TYPE_CHECKING, Any, Optional, Union

from endplay.dealer.generate import generate_deal
from endplay.types import Card, Deal, Denom, Hand, Player

if TYPE_CHECKING:
    from endplay.interact.commandobject import CommandObject


class Action(ABC):
    @abstractproperty
    def name(self) -> str: ...

    @abstractmethod
    def apply(self, cmdobj: "CommandObject") -> Any: ...

    @abstractmethod
    def unapply(self, cmdobj: "CommandObject"): ...


class ActionNotAppliedError(RuntimeError):
    pass


class SetTrumpAction(Action):
    def __init__(self, trump: Denom):
        self.trump = trump
        self.prev_trump: Optional[Denom] = None

    def apply(self, cmdobj):
        self.prev_trump = cmdobj.deal.trump
        cmdobj.deal.trump = self.trump

    def unapply(self, cmdobj):
        if self.prev_trump is None:
            raise ActionNotAppliedError
        cmdobj.deal.trump = self.prev_trump
        self.prev_trump = None

    @property
    def name(self):
        return f"set trump to {self.trump.name}"


class SetFirstAction(Action):
    def __init__(self, first: Player):
        self.first = first
        self.prev_first: Optional[Player] = None

    def apply(self, cmdobj):
        if len(cmdobj.deal.curtrick) != 0:
            raise RuntimeError("trick must be empty to set player on lead")
        self.prev_first = cmdobj.deal.first
        cmdobj.deal.first = self.first

    def unapply(self, cmdobj):
        if self.prev_first is None:
            raise ActionNotAppliedError
        cmdobj.deal.first = self.prev_first
        self.prev_first = None

    @property
    def name(self):
        return f"set first to {self.first.name}"


class PlayAction(Action):
    def __init__(self, card: Union[Card, str]):
        self.card = card
        self.prev_trick: Optional[tuple[Player, list[Card]]] = None

    def apply(self, cmdobj):
        if len(cmdobj.deal.curtrick) == 3:
            self.prev_trick = (cmdobj.deal.first, cmdobj.deal.curtrick)
        cmdobj.deal.play(self.card)

    def unapply(self, cmdobj):
        if self.prev_trick is None:
            cmdobj.deal.unplay()
        else:
            first, curtrick = self.prev_trick
            cmdobj.deal[first.rho].add(self.card)
            cmdobj.deal._data.first = first
            for card in curtrick:
                cmdobj.deal.play(card, False)
        self.prev_trick = None

    @property
    def name(self):
        return f"play card {self.card}"


class UnplayAction(Action):
    def __init__(self):
        self.unplayed_card: Optional[Card] = None

    def apply(self, cmdobj):
        self.unplayed_card = cmdobj.deal.unplay()

    def unapply(self, cmdobj):
        if self.unplayed_card is None:
            raise ActionNotAppliedError
        cmdobj.deal.play(self.unplayed_card)
        self.unplayed_card = None

    @property
    def name(self):
        return "unplay card"


class SetHandAction(Action):
    def __init__(self, player: Player, hand: Union[Hand, str]):
        self.player = player
        self.hand = hand
        self.prev_hand: Optional[Hand] = None

    def apply(self, cmdobj):
        self.prev_hand = cmdobj.deal.__getitem__(self.player).copy()
        cmdobj.deal.__setitem__(self.player, self.hand)

    def unapply(self, cmdobj):
        if self.prev_hand is None:
            raise ActionNotAppliedError
        cmdobj.deal.__setitem__(self.player, self.prev_hand)
        self.prev_hand = None

    @property
    def name(self):
        return f"set {self.player.name} hand to {self.hand}"


class GetHandAction(Action):
    def __init__(self, player: Player):
        self.player = player
        self.prev_hand: Optional[Hand] = None

    def apply(self, cmdobj):
        self.prev_hand = cmdobj.deal.__getitem__(self.player).copy()
        return cmdobj.deal.__getitem__(self.player)

    def unapply(self, cmdobj):
        if self.prev_hand is None:
            raise ActionNotAppliedError
        cmdobj.deal.__setitem__(self.player, self.prev_hand)
        self.prev_hand = None

    @property
    def name(self):
        return f"get hand of {self.player.name}"


class DealAction(Action):
    def __init__(self, pbn: str):
        self.pbn = pbn
        self.prev_deal: Optional[Deal] = None

    def apply(self, cmdobj):
        self.prev_deal = cmdobj.deal.copy()

        new_deal = Deal(self.pbn)
        for player, hand in new_deal:
            cmdobj.deal[player] = hand
        while len(cmdobj.deal.curtrick) > 0:
            cmdobj.deal.unplay(False)

    def unapply(self, cmdobj):
        if self.prev_deal is None:
            raise ActionNotAppliedError

        cmdobj.deal.clear()
        for player, hand in self.prev_deal:
            cmdobj.deal[player] = hand
        for card in self.prev_deal.curtrick:
            cmdobj.deal.play(card, False)
        self.prev_deal = None

    @property
    def name(self):
        return "deal " + self.pbn


class ShuffleAction(DealAction):
    def __init__(self, *constraints: str):
        new_deal = generate_deal(*constraints)
        super().__init__(new_deal.to_pbn())

    @property
    def name(self):
        return "shuffle deal"


class SetBoardAction(Action):
    def __init__(self, board_no: int):
        self.board_no = board_no
        self.prev_board_no: Optional[int] = None

    def apply(self, cmdobj):
        self.prev_board_no = cmdobj.board
        cmdobj.board = self.board_no

    def unapply(self, cmdobj):
        if self.prev_board_no is None:
            raise ActionNotAppliedError
        cmdobj.board = self.prev_board_no
        self.prev_board_no = None

    @property
    def name(self):
        return f"set board to {self.board_no}"
