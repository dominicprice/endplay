"""
Actions class for producing HTML output
"""

__all__ = ["HTMLActions"]

from io import StringIO

import matplotlib.pyplot as plt  # type: ignore

import endplay.stats as stats
from endplay.dealer.actions.base import BaseActions, BaseActionsWriter
from endplay.types import Denom, Player, Vul


class HTMLActions(BaseActions):
    def open(self, fname, deals) -> "HTMLActionsWriter":
        return HTMLActionsWriter(self, fname, deals)


class HTMLActionsWriter(BaseActionsWriter):
    def on_enter(self):
        self.write(preamble)

    def on_exit(self):
        self.write(postamble)

    def print(self, *players):
        compass = '<div class="compass">'
        for player in Player.iter_order("NWES"):
            compass += f'<div class="{player.name}">{player.abbr}</div>'
        compass += "</div>"
        box = "<div></div>"
        self.write("<div>")
        for i, deal in enumerate(self.deals, 1):
            if self.actions.board_numbers:
                info = f'<div class="board-info"><div>Board {i}</div>'
                info += f"<div>Vul {Vul.from_board(i).abbr}</div><div>"
                info += f"{Player((i-1) % 4).abbr} deals</div></div>"
            else:
                info = box
            hands = {}
            for player in Player:
                if player in players:
                    h = f'<div class="hand {player.name}">'
                    for denom in Denom.suits():
                        holding = str(deal[player][denom]) or "&mdash;"
                        h += f'<div class="{denom.name}">{holding}</div>'
                    hands[player] = h + "</div>"
                else:
                    hands[player] = r'<div class="hand {player.name}"></div>'
            self.write('<div class="deal" style="margin: 20px">')
            self.write(
                info,
                hands[Player.north],
                box,
                hands[Player.west],
                compass,
                hands[Player.east],
                box,
                hands[Player.south],
                box,
            )
            self.write("</div>")
        self.write("</div>")

    def printpbn(self):
        self.write('<table class="deal-oneline">')
        self.write("<tr>", end="")
        if self.actions.board_numbers:
            self.write("<th>#</th>", end="")
        self.write("<th>PBN</th>", end="")
        self.write("</tr>")
        for i, deal in enumerate(self.deals, 1):
            self.write("<tr>", end="")
            if self.actions.board_numbers:
                self.write(f'<td><div class="value">{i}</div></td>', end="")
            self.write(f'<td><div class="hand-inline">{str(deal)}</div></td>')
            self.write("</tr>")
        self.write("</table>")

    def printcompact(self, expr=None):
        self.write('<table class="deal-compact">')
        self.write("<tr>")
        if self.actions.board_numbers:
            self.write("<th>#</th>")
        self.write("<th>North</th><th>East</th><th>South</th><th>West</th>", end="")
        if expr is not None:
            self.write("<th>Value</th>", end="")
        self.write("</tr>")
        for i, deal in enumerate(self.deals, 1):
            self.write("<tr>")
            if self.actions.board_numbers:
                self.write(f'<td><div class="value">{i}</div></td>', end="")
            for player in Player:
                self.write('<td><div class="hand">')
                for denom in Denom.suits():
                    holding = str(deal[player][denom]) or "&mdash;"
                    self.write(f'<div class="{denom.name}">{holding}</div>')
                self.write("</div></td>")
            if expr is not None:
                self.write(f'<td><div class="value">{expr(deal)}</div></td>')
            self.write("</tr>")
        self.write("</table>")

    def printoneline(self, expr=None):
        self.write('<table class="deal-oneline">')
        self.write("<tr>", end="")
        if self.actions.board_numbers:
            self.write("<th>#</th>", end="")
        self.write("<th>North</th><th>East</th><th>South</th><th>West</th>", end="")
        if expr is not None:
            self.write("<th>Value</th>", end="")
        self.write("</tr>")
        for i, deal in enumerate(self.deals, 1):
            self.write("<tr>")
            if self.actions.board_numbers:
                self.write(f'<td><div class="value">{i}</div></td>', end="")
            for player in Player:
                self.write('<td><div class="hand-inline">')
                for denom in Denom.suits():
                    holding = str(deal[player][denom]) or "&mdash;"
                    self.write(f'<div class="{denom.name} inline">{holding}</div>')
                self.write("</div></td>")
            if expr is not None:
                self.write(f'<td><div class="value">{expr(deal)}</div></td>')
            self.write("</tr>")
        self.write("</table>")

    def printes(self, *objs):
        self.write('<table class="deal-oneline">')
        self.write("<tr>", end="")
        if self.actions.board_numbers:
            self.write("<th>#</th>", end="")
        self.write("<th>Output</th>", end="")
        self.write("</tr>")
        for i, deal in enumerate(self.deals, 1):
            self.write("<tr>", end="")
            if self.actions.board_numbers:
                self.write(f'<td><div class="value">{i}</div></td>', end="")
            self.write('<td><div class="value">')
            for obj in objs:
                if callable(obj):
                    self.write(obj(deal), end="")
                else:
                    self.write(str(obj).replace("\n", "<br>"), end="")
            self.write("</div></td>")
            self.write("</tr>")
        self.write("</table>")

    def average(self, expr, s=None):
        if s is None:
            s = ""
        self.write(
            '<div class="valuebox">', s, stats.average(self.deals, expr), "</div>"
        )

    def frequency1d(self, expr, lb, ub, s=None):
        hist = stats.frequency(self.deals, expr, lb, ub)
        fig, ax = plt.subplots()
        ax.bar(list(range(lb, ub + 1)), hist)
        if s:
            ax.set_title(s)
        f = StringIO()
        fig.savefig(f, format="svg")
        self.write('<div class="valuebox">', f.getvalue(), "</div>")

    def frequency2d(self, ex1, lb1, ub1, ex2, lb2, ub2, s=None):
        hist = stats.cofrequency(self.deals, ex1, ex2, lb1, ub1, lb2, ub2)
        fig, ax = plt.subplots()
        m = ax.matshow(hist)
        fig.colorbar(m)
        ax.set_xticks(list(range(1 + ub2 - lb2)))
        ax.set_xticklabels([str(i) for i in range(lb2, ub2 + 1)])
        ax.set_yticks(list(range(1 + ub1 - lb1)))
        ax.set_yticklabels([str(i) for i in range(lb1, ub1 + 1)])
        if s:
            ax.set_title(s)
        f = StringIO()
        fig.savefig(f, format="svg")
        self.write('<div class="valuebox">', f.getvalue(), "</div>")


preamble = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Dealer output</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Overpass+Mono:wght@400&display=swap" rel="stylesheet">
    <style>
        html, body {
            padding: 0;
            margin: 0;
        }

        body {
            background-color: slategray;
        }

        .content {
            background-color: white;
            min-width: 600px;
            margin: 50px;
            padding: 20px;
            border: 5px solid #aaa;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .deal {
            font-size: 16px;
            border: 1px solid #ddd;
            display: inline-flex;
            flex-flow: row wrap;
            width: 360px;
            justify-content: space-between;
            font-family: sans-serif;
            background-color: #fafafa;
            padding: 5px;
            border-radius: 5px;
        }

            .deal > div {
                padding: 10px;
                flex-basis: 100px;
                height: 100px;
            }

        .board-info {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            gap: 5px;
        }

        .hand {
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 3px;
            font-family: "Overpass Mono", sans-serif;
            background-color: #f2efd0;
            overflow-wrap: anywhere;
            word-break: break-all;
            letter-spacing: 2px;
        }

        .hand-inline {
            display: flex;
            flex-direction: row;
            justify-content: center;
            gap: 3px;
            font-family: "Overpass Mono", sans-serif;
            background-color: #edfaa5;
            letter-spacing: 2px;
            padding: 5px;
        }

        .deal > .hand.north {
            border-radius: 5px 5px 0px 0px;
        }

        .deal > .hand.east {
            border-radius: 0px 5px 5px 0px;
        }

        .deal > .hand.south {
            border-radius: 0px 0px 5px 5px;
        }

        .deal > .hand.west {
            border-radius: 5px 0px 0px 5px;
        }

        .spades, .hearts, .diamonds, .clubs {
            text-indent: -16px;
            margin-left: 16px;
        }

            .spades:before, .hearts:before, .diamonds:before, .clubs:before {
                display: inline-block;
                width: 16px;
                text-indent: 0px;
            }

            .spades:before {
                content: "♠ ";
                color: #01039e;
            }

            .hearts:before {
                content: "♥ ";
                color: #a00203;
            }

            .diamonds:before {
                content: "♦ ";
                color: #c05e0a;
            }

            .clubs:before {
                content: "♣ ";
                color: #036a03;
            }

        .compass {
            display: flex;
            flex-flow: row wrap;
            color: white;
            background-color: #106610;
            align-items: center;
            font-weight: bold;
            user-select: none;
        }

            .compass .north {
                flex-basis: 100%;
                text-align: center;
            }

            .compass .west {
                flex-basis: 50%;
                text-align: left;
            }

            .compass .east {
                flex-basis: 50%;
                text-align: right;
            }

            .compass .south {
                flex-basis: 100%;
                text-align: center;
            }

        .dealer {
            text-decoration: underline;
        }

        .vul {
            color: #ff7777;
        }

        .nonvul {
            color: #77ff77;
        }

        .deal-compact {
            border-collapse: collapse;
        }

            .deal-compact .hand {
                padding: 10px;
            }

            .deal-compact th {
                color: white;
                font-weight: bold;
                background-color: #106610;
                font-family: sans-serif;
                padding: 5px;
            }

            .deal-compact td > div {
                width: 175px;
                height: 80px;
            }

            .deal-compact .value {
                background-color: #eee;
                height: 102px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: sans-serif;
            }

        .deal-oneline {
            border-collapse: collapse;
        }

            .deal-oneline .hand {
                padding: 10px;
            }

            .deal-oneline th {
                color: white;
                font-weight: bold;
                background-color: #106610;
                font-family: sans-serif;
                padding: 5px;
            }

            .deal-oneline .value {
                background-color: #eee;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: sans-serif;
            }

        .valuebox {
            background-color: #eee;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 50px;
            font-family: sans-serif;
        }
    </style>
</head>
<body>
    <div class="content">
"""

postamble = r"""
</div>
</body>
</html>
"""
