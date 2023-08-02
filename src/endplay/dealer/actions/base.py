"""
Base actions class to provide the interface.
"""

__all__ = ["BaseActions"]

import sys
from abc import ABC, abstractmethod
from typing import List, Optional, TextIO, Union

from endplay.dealer.constraint import ConstraintInterpreter, Expr
from endplay.parsers.dealer import Node
from endplay.types import Deal, Player, Vul


class BaseActions(ABC):
    def __init__(
        self,
        board_numbers: bool,
        vul: Optional[Vul],
        dealer: Optional[Player],
        interp: ConstraintInterpreter,
    ):
        self.board_numbers = board_numbers
        self.vul = vul
        self.dealer = dealer
        self.interp = interp

    @abstractmethod
    def open(self, fname: Optional[str], deals: List[Deal]) -> "BaseActionsWriter":
        ...


class BaseActionsWriter(ABC):
    def __init__(self, actions: BaseActions, fname: Optional[str], deals: List[Deal]):
        self.actions = actions
        self.deals = deals
        self.fname = fname
        self.f: Optional[TextIO] = None

    def __enter__(self):
        if self.fname is None:
            self.f = sys.stdout
            self.closef = False
        else:
            self.f = open(self.fname, "w")
            self.closef = True
        self.on_enter()
        return self

    def __exit__(self, *_):
        self.on_exit()
        if self.f and self.closef:
            self.f.close()
            self.closef = False
        self.f = None

    def write(self, *objs, **kwargs):
        if self.f is None:
            raise RuntimeError("stream is not open for writing")
        if "file" in kwargs:
            raise RuntimeError(
                "Unexpected keyword argument 'file' passed to BaseActions.write"
            )
        print(*objs, **kwargs, file=self.f)

    def run_action(self, node: Node):
        if node.value == "printall":
            self.printall()
        elif node.value == "print":
            self.print(*[child.value for child in node.children])
        elif node.value == "printew":
            self.printew()
        elif node.value == "printpbn":
            self.printpbn()
        elif node.value == "printcompact":
            if len(node.children) == 0:
                expr = None
            else:
                expr = self.actions.interp.lambdify(node.first_child)
            self.printcompact(expr)
        elif node.value == "printoneline":
            if len(node.children) == 0:
                expr = None
            else:
                expr = self.actions.interp.lambdify(node.first_child)
            self.printoneline(expr)
        elif node.value == "printes":
            objs = []
            for child in node.children:
                if child.dtype == Node.VALUE:
                    objs.append(child.value)
                else:
                    objs.append(self.actions.interp.lambdify(child))
            self.printes(*objs)
        elif node.value == "average":
            if len(node.children) == 2:
                s, expr = node.first_child.value, self.actions.interp.lambdify(
                    node.last_child
                )
            else:
                s, expr = None, self.actions.interp.lambdify(node.last_child)
            self.average(expr, s)
        elif node.value == "frequency":
            if node.first_child.dtype == Node.VALUE:
                s, args = node.children[0].value, node.children[1:]
            else:
                s, args = None, node.children
            ex1, lb1, ub1 = (
                self.actions.interp.lambdify(args[0]),
                args[1].value,
                args[2].value,
            )
            if len(args) > 3:
                ex2, lb2, ub2 = (
                    self.actions.interp.lambdify(args[3]),
                    args[4].value,
                    args[5].value,
                )
                self.frequency2d(ex1, lb1, ub1, ex2, lb2, ub2, s)
            else:
                self.frequency1d(ex1, lb1, ub1, s)
        else:
            raise ValueError(f"Unknown action {node.value}")

    @abstractmethod
    def on_enter(self):
        ...

    @abstractmethod
    def on_exit(self):
        ...

    @abstractmethod
    def print(self, *players: Player):
        ...

    def printew(self):
        self.print(Player.east, Player.west)

    def printall(self):
        self.print(*Player)

    @abstractmethod
    def printpbn(self):
        ...

    @abstractmethod
    def printcompact(self, expr: Optional[Expr] = None):
        ...

    @abstractmethod
    def printoneline(self, expr: Optional[Expr] = None):
        ...

    @abstractmethod
    def printes(self, *objs: Union[Expr, str]):
        ...

    @abstractmethod
    def average(self, expr: Expr, s: Optional[str] = None):
        ...

    @abstractmethod
    def frequency1d(
        self,
        expr: Expr,
        lower_bound: float,
        upper_bound: float,
        s: Optional[str] = None,
    ):
        ...

    @abstractmethod
    def frequency2d(
        self,
        ex1: Expr,
        lb1: float,
        hb1: float,
        ex2: Expr,
        lb2: float,
        hb2: float,
        s: Optional[str] = None,
    ):
        ...
