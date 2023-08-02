"""
Exposes the `CommandObject` class which can be used to perform actions on a
`Deal` object while maintaining a history of the actions applied so that they
can be undone and redone.
"""

__all__ = ["CommandError", "CommandObject"]

import functools
import textwrap
from collections.abc import Callable
from inspect import Parameter, signature
from typing import Any, Generic, Optional, Protocol, TypeVar, Union

from endplay.evaluate import hcp
from endplay.interact.actions import (
    Action,
    DealAction,
    PlayAction,
    SetBoardAction,
    SetFirstAction,
    SetHandAction,
    SetTrumpAction,
    ShuffleAction,
    UnplayAction,
)
from endplay.types.card import Card
from endplay.types.deal import Deal
from endplay.types.denom import Denom
from endplay.types.hand import Hand
from endplay.types.player import Player

try:
    from typing import get_args, get_origin
except ImportError:
    from typing_extensions import get_args  # type: ignore[no-redef]
    from typing_extensions import get_origin  # type: ignore[no-redef]

T = TypeVar("T")


class CommandError(RuntimeError):
    """
    Exception raised if an error occurred whilst trying to perform a command.
    """

    pass


class Commandable(Protocol):
    """
    Protocol which matches the function signature of a `CommandObject` method
    with the `command` decorator applied.
    """

    def __call__(self, _self: "CommandObject", *args: str) -> Optional[str]:
        ...


class command(Generic[T]):
    """
    `command` is a decorator which converts a `CommandObject` method into a
    function which takes a varargs of strings as arguments and returns an
    optional string. The conversion is done via the arguments to the command
    decorator, the first argument should convert the return value of the method
    into a string, or be `None` if the functions returns `None`. The rest of
    the arguments should convert a string to the corresponding argument in the
    method. If the last argument in the method is *args, then the last
    converter in given to the decorator is used to convert all the varargs.

    Example:
    ```
    class CommandObject:
        ... # rest of class

        @command(str, int)
        def cmd_addone(self, i: int) -> int:
            return i + 1
    ```
    The resulting function is equivalent to
    ```
        def cmd_addone(self, arg1: str) -> str:
            def inner(self, i: int) -> int:
                return i + 1
            res = inner(self, int(arg1))
            return str(res)
    ```
    """

    def __init__(
        self, r_conv: Callable[[T], Optional[str]], *p_conv: Callable[[str], Any]
    ):
        self.r_conv = r_conv
        self.p_conv = p_conv

    def __call__(self, f: Callable[..., T]) -> Commandable:
        @functools.wraps(f)
        def inner(_self: "CommandObject", *args: str) -> Optional[str]:
            arglist = []
            for i, arg in enumerate(args):
                # if we run out of converters then we have hit an *args
                # so keep using the last converter
                converter = self.p_conv[min(i, len(self.p_conv) - 1)]
                arglist += [converter(arg)]

            res = f(_self, *arglist)
            return self.r_conv(res)

        return inner


def ReturnNone(_: None) -> None:
    return None


class CommandObject:
    def __init__(self, deal: Optional[Deal] = None):
        self.deal = deal or Deal()
        self.tricks_ns: list[list[Card]] = []
        self.tricks_ew: list[list[Card]] = []
        self.board = 1
        self.history: list[Action] = []
        self.future: list[Action] = []

    def apply_action(self, action: Action) -> None:
        action.apply(self)
        self.history.append(action)
        self.future = []

    def dispatch(self, cmdline: list[str]) -> Optional[str]:
        cmd, *args = cmdline
        if hasattr(self, "cmd_" + cmd):
            return getattr(self, "cmd_" + cmd)(*args)
        raise CommandError("unknown command: " + cmd)

    @command(str, str)
    def cmd_help(self, cmd_name: Optional[str] = None) -> str:
        """
        Displays all available commands. If cmd_name is given, provide help
        about that command.
        """
        if cmd_name is None:
            cmds = [
                fname.removeprefix("cmd_")
                for fname in vars(CommandObject)
                if fname.startswith("cmd_")
            ]
            return "\n".join(cmds)
        if hasattr(CommandObject, "cmd_" + cmd_name):
            cmd = getattr(CommandObject, "cmd_" + cmd_name)
            usage = "usage: " + cmd_name + " "
            for param in signature(cmd).parameters.values():
                if param.name == "self":
                    continue
                elif param.kind == Parameter.POSITIONAL_OR_KEYWORD:
                    if get_origin(param.annotation) is Union and type(None) in get_args(
                        param.annotation
                    ):
                        usage += "[" + param.name + "] "
                    else:
                        usage += param.name + " "
                elif param.kind == Parameter.VAR_POSITIONAL:
                    usage += param.name + " [" + param.name + "...] "
            doc = cmd.__doc__ or ""
            return usage + "\n" + textwrap.dedent(doc).strip()
        raise CommandError("unknown command: " + cmd_name)

    @command(str, str)
    def cmd_history(self) -> str:
        """
        Displays the undo and redo history. An asterisk is displayed in front
        of the action which would be applied if redo is called.
        """
        history = ["" + action.name for action in self.history]
        cur = [">>> you are here <<<"]
        future = ["" + action.name for action in self.future]
        return "\n".join(history + cur + future)

    @command(Deal.to_pbn, str)
    def cmd_shuffle(self, *constraints: str) -> Deal:
        """
        Shuffles the deal according to the given constraints which should be
        given in dealer format. Ensure constrains are surrounded by quotes to
        avoid being split by whitespace.
        """
        action = ShuffleAction(*constraints)
        self.apply_action(action)
        return self.deal

    @command(Deal.to_pbn, str)
    def cmd_deal(self, pbn: str) -> Deal:
        """
        Deals the given pbn string to the players
        """
        action = DealAction(pbn)
        self.apply_action(action)
        return self.deal

    @command(str, int)
    def cmd_board(self, board: Optional[int] = None) -> int:
        """
        Displays the board number, and optionally changes the board number to
        the argument if given.
        """
        if board is not None:
            action = SetBoardAction(board)
            self.apply_action(action)
        return self.board

    @command(lambda d: d.name, Denom.find)  # type: ignore
    def cmd_trump(self, denom: Optional[Denom] = None) -> Denom:
        """
        Displays the trump suit, and optionally changes the trump suit to the
        argument if given.
        """
        if denom is not None:
            action = SetTrumpAction(denom)
            self.apply_action(action)
        return self.deal.trump

    @command(lambda p: p.name, Player.find)  # type: ignore
    def cmd_first(self, player: Optional[Player] = None) -> Player:
        """
        Displays the player on lead to the first card of the current trick, or
        changes the player on lead if the argument is given.
        """
        if player is not None:
            action = SetFirstAction(player)
            self.apply_action(action)
        return self.deal.first

    @command(ReturnNone, Card)
    def cmd_play(self, *cards: Card) -> None:
        """
        Plays the specified sequence of cards to the current trick.
        """
        if len(cards) == 0:
            raise CommandError("no cards specified to play")
        for card in cards:
            action = PlayAction(card)
            self.apply_action(action)

    @command(ReturnNone)
    def cmd_unplay(self) -> None:
        """
        Unplays the last card played to the trick.
        """
        action = UnplayAction()
        self.apply_action(action)

    @command(lambda p: p.name, Hand)  # type: ignore
    def cmd_hand(self, player: Player, hand: Optional[Hand] = None) -> Hand:
        """
        Displays the hand of the given player, or changes the player's hand to
        a PBN string if the hand argument is given.
        """
        if hand is not None:
            action = SetHandAction(player, hand)
            self.apply_action(action)
        return self.deal[player]

    @command(str, Player.find)
    def cmd_hcp(self, player: Player) -> float:
        """
        Displays the number of high card points in the given player's hand.
        """
        return hcp(self.deal[player])

    @command(ReturnNone)
    def cmd_rewind(self) -> None:
        """
        Rewinds to the beginning of the history.
        """
        while self.history:
            CommandObject.cmd_undo(self)

    @command(ReturnNone)
    def cmd_fastforward(self) -> None:
        """
        Fast-forwards to the end of the history.
        """
        while self.future:
            CommandObject.cmd_redo(self)

    @command(ReturnNone)
    def cmd_checkpoint(self) -> None:
        """
        Removes all past actions in the history.
        """
        self.history = []

    @command(ReturnNone)
    def cmd_undo(self) -> None:
        """
        Undoes the last action.
        """
        if len(self.history) == 0:
            raise CommandError("reached start of history")
        action = self.history.pop()
        action.unapply(self)
        self.future.append(action)

    @command(ReturnNone)
    def cmd_redo(self) -> None:
        """
        Redoes the next action.
        """
        if len(self.future) == 0:
            raise CommandError("reached end of history")
        action = self.future.pop()
        action.apply(self)
        self.history.append(action)

    @command(ReturnNone)
    def cmd_exit(self) -> None:
        """
        Exits the program.
        """
        raise SystemExit
