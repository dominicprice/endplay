from __future__ import annotations

import inspect

"""
Exposes the `CommandObject` class which can be used to perform actions on a
`Deal` object while maintaining a history of the actions applied so that they
can be undone and redone.
"""

__all__ = ["CommandError", "CommandObject"]

import logging
import textwrap
from collections.abc import Callable
from inspect import Parameter, signature
from typing import Any, Generic, Optional, TypeVar, Union

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

logging.basicConfig(filename="/home/dominic/curses.txt")


class CommandError(RuntimeError):
    """
    Exception raised if an error occurred whilst trying to perform a command.
    """

    pass


def ReturnNone(_: None) -> None:
    return None


commands: dict[str, "Command"] = {}


def _gen_usage(name: str, f: Callable[..., Any]):
    """
    Creates a usage message from a CommandObject `cmd_` method
    """
    usage = name + " "
    self_param, *params = signature(f).parameters.values()
    if self_param.name != "self":
        raise RuntimeError("first parameter should be 'self'")
    for param in params:
        if param.kind in [Parameter.POSITIONAL_OR_KEYWORD, Parameter.POSITIONAL_ONLY]:
            if param.default is not inspect._empty:
                usage += "[" + param.name + "] "
            else:
                usage += param.name + " "
        elif param.kind == Parameter.VAR_POSITIONAL:
            name = param.name if param.name[-1] != "s" else param.name[:-1]
            usage += "[" + name + " [" + name + "...]] "
        else:
            raise RuntimeError("only positional arguments are supported")
    return usage


class Command(Generic[T]):
    """
    Wraps a CommandObject method and provides a call method which can
    invoke the underlying function by passing in arguments as strings
    which are converted into the correct parameter types using the conv
    functions.
    """

    def __init__(
        self,
        f: Callable[..., T],
        r_conv: Callable[[T], Optional[str]],
        *p_conv: Callable[[str], Any],
    ):
        self.f = f
        self.r_conv = r_conv
        self.p_conv = p_conv
        if not f.__name__.startswith("cmd_"):
            raise NameError("cmd name must start with cmd_")
        self.name = f.__name__[4:]
        self.usage = _gen_usage(self.name, f)
        self.doc = textwrap.dedent(f.__doc__ or "")

    @property
    def help(self):
        return "usage: " + self.usage + "\n" + self.doc

    def __call__(self, cmdobj: "CommandObject", *args: str):
        arglist = []
        for i, arg in enumerate(args):
            c = self.p_conv[min(i, len(self.p_conv) - 1)]
            arglist += [c(arg)]

        res = self.f(cmdobj, *arglist)
        return self.r_conv(res)

    @staticmethod
    def cmd(r_conv: Callable[[T], Optional[str]], *p_conv: Callable[[str], Any]):
        """
        Decorator which produces a Command object from a CommandObject method
        """

        def inner(f: Callable[..., T]):
            c = Command(f, r_conv, *p_conv)
            commands[c.name] = c
            return f

        return inner


class CommandObject:
    """
    CommandObject provides an interface for interacting with a deal using actions
    which are pushed onto an internal history allowing them to be undone and
    redone. The `cmd_` methods can be called normally, or `dispatch` can be called
    with a shell like argument list to invoke one of the `cmd_` methods.
    """

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
        c = commands.get(cmd)
        if c is None:
            raise CommandError("unknown command: " + cmd)
        return c(self, *args)

    @Command.cmd(str, str)
    def cmd_help(self, cmd_name: Optional[str] = None) -> str:
        """
        Displays all available commands. If cmd_name is given, provide help
        about that command.

        Example 1: help
        Example 2: help shuffle
        """
        if cmd_name is None:
            return "\n".join(cmd.usage for cmd in commands.values())

        c = commands.get(cmd_name)
        if c is None:
            raise CommandError("unknown command: " + cmd_name)
        return c.help

    @Command.cmd(str, str)
    def cmd_history(self) -> str:
        """
        Displays the undo and redo history. An asterisk is displayed in front
        of the action which would be applied if redo is called.
        """
        history = ["" + action.name for action in self.history]
        cur = [">>> you are here <<<"]
        future = ["" + action.name for action in self.future]
        return "\n".join(history + cur + future)

    @Command.cmd(Deal.to_pbn, str)
    def cmd_shuffle(self, *constraints: str) -> Deal:
        """
        Shuffles the deal according to the given constraints which should be
        given in dealer format. Ensure constrains are surrounded by quotes to
        avoid being split by whitespace.
        """
        action = ShuffleAction(*constraints)
        self.apply_action(action)
        return self.deal

    @Command.cmd(Deal.to_pbn, str)
    def cmd_deal(self, pbn: str) -> Deal:
        """
        Deals the given pbn string to the players
        """
        action = DealAction(pbn)
        self.apply_action(action)
        return self.deal

    @Command.cmd(str, int)
    def cmd_board(self, board: Optional[int] = None) -> int:
        """
        Displays the board number, and optionally changes the board number to
        the argument if given.
        """
        if board is not None:
            action = SetBoardAction(board)
            self.apply_action(action)
        return self.board

    @Command.cmd(lambda d: d.name, Denom.find)  # type: ignore
    def cmd_trump(self, denom: Optional[Denom] = None) -> Denom:
        """
        Displays the trump suit, and optionally changes the trump suit to the
        argument if given.
        """
        if denom is not None:
            action = SetTrumpAction(denom)
            self.apply_action(action)
        return self.deal.trump

    @Command.cmd(lambda p: p.name, Player.find)  # type: ignore
    def cmd_first(self, player: Optional[Player] = None) -> Player:
        """
        Displays the player on lead to the first card of the current trick, or
        changes the player on lead if the argument is given.
        """
        if player is not None:
            action = SetFirstAction(player)
            self.apply_action(action)
        return self.deal.first

    @Command.cmd(ReturnNone, Card)
    def cmd_play(self, card: Card, *cards: Card) -> None:
        """
        Plays the specified sequence of cards to the current trick.
        """
        action = PlayAction(card)
        self.apply_action(action)

        for c in cards:
            action = PlayAction(c)
            self.apply_action(action)

    @Command.cmd(ReturnNone)
    def cmd_unplay(self) -> None:
        """
        Unplays the last card played to the trick.
        """
        action = UnplayAction()
        self.apply_action(action)

    @Command.cmd(lambda p: p.name, Hand)  # type: ignore
    def cmd_hand(self, player: Player, hand: Optional[Hand] = None) -> Hand:
        """
        Displays the hand of the given player, or changes the player's hand to
        a PBN string if the hand argument is given.
        """
        if hand is not None:
            action = SetHandAction(player, hand)
            self.apply_action(action)
        return self.deal[player]

    @Command.cmd(str, Player.find)
    def cmd_hcp(self, player: Player) -> float:
        """
        Displays the number of high card points in the given player's hand.
        """
        return hcp(self.deal[player])

    @Command.cmd(ReturnNone)
    def cmd_rewind(self) -> None:
        """
        Rewinds to the beginning of the history.
        """
        while self.history:
            CommandObject.cmd_undo(self)

    @Command.cmd(ReturnNone)
    def cmd_fastforward(self) -> None:
        """
        Fast-forwards to the end of the history.
        """
        while self.future:
            CommandObject.cmd_redo(self)

    @Command.cmd(ReturnNone)
    def cmd_checkpoint(self) -> None:
        """
        Removes all past actions in the history.
        """
        self.history = []

    @Command.cmd(ReturnNone)
    def cmd_undo(self) -> None:
        """
        Undoes the last action.
        """
        if len(self.history) == 0:
            raise CommandError("reached start of history")
        action = self.history.pop()
        action.unapply(self)
        self.future.append(action)

    @Command.cmd(ReturnNone)
    def cmd_redo(self) -> None:
        """
        Redoes the next action.
        """
        if len(self.future) == 0:
            raise CommandError("reached end of history")
        action = self.future.pop()
        action.apply(self)
        self.history.append(action)

    @Command.cmd(ReturnNone)
    def cmd_exit(self) -> None:
        """
        Exits the program.
        """
        raise SystemExit
