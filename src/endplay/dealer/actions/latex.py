"""
Actions class for producing LaTeX output.
"""

__all__ = ["LaTeXActions"]

import endplay.stats as stats
from endplay.dealer.actions.base import BaseActions, BaseActionsWriter
from endplay.types import Denom, Player


class LaTeXActions(BaseActions):
    def open(self, fname, deals):
        return LaTeXActionsWriter(self, fname, deals)


class LaTeXActionsWriter(BaseActionsWriter):
    def on_enter(self):
        self.write(preamble)

    def on_exit(self):
        self.write(postamble)

    def print(self, *players):
        exclude = [p for p in Player if p not in players]
        self.write(r"\noindent ")
        for deal in self.deals:
            self.write(
                r"\resizebox{0.33\textwidth}{!}{" + deal.to_LaTeX(exclude=exclude) + "}"
            )

    def printpbn(self):
        for deal in self.deals:
            self.write(str(deal))

    def printcompact(self, expr=None):
        if expr is None:
            expr = lambda _: ""
        for deal in self.deals:
            self.write(r"\begin{tabular}{l | l | l | l | l | l}")
            self.write(
                r"& \textbf{North} & \textbf{East} & \textbf{South} & \textbf{West} & \textbf{Value} \\ \hline"
            )
            self.write(
                r"$\spadesuit$ &",
                " & ".join(str(deal[p][Denom.spades]) for p in Player),
                r"& \\ ",
            )
            self.write(
                r"$\heartsuit$ &",
                " & ".join(str(deal[p][Denom.hearts]) for p in Player),
                "&",
                expr(deal),
                r"\\ ",
            )
            self.write(
                r"$\diamondsuit$ &",
                " & ".join(str(deal[p][Denom.diamonds]) for p in Player),
                r"& \\ ",
            )
            self.write(
                r"$\clubsuit$ &",
                " & ".join(str(deal[p][Denom.clubs]) for p in Player),
                r"& \\ ",
            )
            self.write(r"\end{tabular} \\ ")

    def printoneline(self, expr=None):
        for deal in self.deals:
            for player in Player:
                self.write(player.abbr, end=":")
                for denom in Denom.suits():
                    self.write(
                        "$\\" + denom.name + "uit$" + str(deal[player][denom]), end=" "
                    )
            if expr is not None:
                self.write(f" [{expr(deal)}]", end=" ")
            self.write(r"\\ ")

    def printes(self, *objs):
        for deal in self.deals:
            for obj in objs:
                if callable(obj):
                    self.write(obj(deal), end="")
                else:
                    self.write(obj, end="")

    def average(self, expr, s=None):
        if s:
            self.write(s, end="")
        self.write(stats.average(self.deals, expr))

    def frequency1d(self, expr, lb, hb, s=None):
        if s:
            self.write(r"\subsection*{" + s + "}")
        hist = stats.frequency(self.deals, expr, lb, hb)
        cols = " | ".join("c" for _ in range(lb, hb + 1))
        self.write(r"\begin{center}")
        self.write(r"\begin{tabular}{| " + cols + "|}")
        self.write(r"\hline")
        self.write(" & ".join(str(i) for i in range(lb, hb + 1)) + r" \\ \hline")
        self.write(" & ".join(str(v) for v in hist) + r" \\ \hline")
        self.write(r"\end{tabular}")
        self.write(r"\end{center}")

    def frequency2d(self, ex1, lb1, hb1, ex2, lb2, hb2, s=None):
        if s:
            self.write(r"\subsection*{" + s + "}")
        hist = stats.cofrequency(self.deals, ex1, ex2, lb1, hb1, lb2, hb2)
        cols = " | ".join("c" for _ in range(lb2, hb2 + 1))
        self.write(r"\begin{center}")
        self.write(r"\begin{tabular}{| c | " + cols + " |}")
        self.write(r"\hline")
        self.write(
            " & " + " & ".join(str(i) for i in range(lb2, hb2 + 1)) + r" \\ \hline"
        )
        for i, row in enumerate(hist, lb1):
            self.write(f"{i} & " + " & ".join(str(v) for v in row) + r" \\ \hline")
        self.write(r"\end{tabular}")
        self.write(r"\end{center}")


preamble = r"""
\documentclass{article}
\begin{document}
"""

postamble = r"""
\end{document}
"""
