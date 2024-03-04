"""
An HTML interface to many of the features of endplay including
dealing hands and performing double-dummy analysis.
"""

import json
import os
import shlex
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional, Union

from endplay.dds.ddtable import calc_dd_table
from endplay.dds.solve import solve_board
from endplay.interact.commandobject import CommandObject
from endplay.interact.frontends.base import BaseFrontend
from endplay.types.denom import Denom
from endplay.types.player import Player
from endplay.types.vul import Vul

g_cmdobj = CommandObject(None)
script_dir = os.path.dirname(os.path.realpath(__file__))


class HTMLFrontend(BaseFrontend):
    def __init__(self, cmdobj: CommandObject):
        global g_cmdobj
        g_cmdobj = cmdobj

        self.host = "localhost"
        self.port = 4928

        self.server = HTTPServer((self.host, self.port), EndplayServer)

    def interact(self):
        addr = f"http://{self.host}:{self.port}"
        webbrowser.open(addr)
        print("serving on", addr)
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.server_close()


class EndplayServer(BaseHTTPRequestHandler):
    def write(self, s: Union[str, dict]):
        if isinstance(s, str):
            self.wfile.write(s.encode("utf-8"))
        else:
            self.wfile.write(json.dumps(s).encode("utf-8"))

    def do_GET(self):
        if self.path == "/":
            self.get_home()
        elif self.path == "/style.css":
            self.get_style()
        elif self.path == "/script.js":
            self.get_script()
        else:
            self.get_notfound()

    def do_POST(self):
        if self.path == "/command":
            self.post_command()
        else:
            self.get_notfound()

    def get_script(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript")
        self.end_headers()

        with open(os.path.join(script_dir, "script.js")) as f:
            self.write(f.read())

    def get_style(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/css")
        self.end_headers()

        with open(os.path.join(script_dir, "style.css")) as f:
            self.write(f.read())

    def get_home(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        with open(os.path.join(script_dir, "index.html")) as f:
            self.write(f.read())

    def post_command(self):
        try:
            content_len = int(self.headers["Content-Length"])
        except KeyError:
            self.send_response(411)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.write({"error": "Content-Length header is required"})
            return

        cmd = self.rfile.read(content_len).decode("utf-8").strip()
        if cmd == "":
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.write({"error": "request body is empty"})

        try:
            output = g_cmdobj.dispatch(shlex.split(cmd))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.write({"error": str(e)})
            return

        history = [""] + [a.name for a in g_cmdobj.history]
        history.extend(a.name for a in reversed(g_cmdobj.future))
        history_idx = len(g_cmdobj.history)
        try:
            s = solve_board(g_cmdobj.deal)
            solutions = [
                {"suit": c.suit.name, "rank": c.rank.abbr, "tricks": t} for c, t in s
            ]
        except Exception:
            solutions = None

        table: Optional[dict[str, dict[str, int]]]
        try:
            if len(g_cmdobj.deal[Player.north]) == 0:
                raise RuntimeError
            t = calc_dd_table(g_cmdobj.deal)
            table = {}
            for player in Player:
                table[player.name] = {}
                for denom in Denom:
                    table[player.name][denom.name] = t[player, denom]
        except Exception:
            table = None

        hcp = {
            player.name: CommandObject.cmd_hcp(g_cmdobj, player) for player in Player
        }

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.write(
            {
                "deal": {
                    "north": g_cmdobj.deal.north.to_pbn(),
                    "east": g_cmdobj.deal.east.to_pbn(),
                    "south": g_cmdobj.deal.south.to_pbn(),
                    "west": g_cmdobj.deal.west.to_pbn(),
                    "first": g_cmdobj.deal.first.name,
                    "trump": g_cmdobj.deal.trump.name,
                    "board_no": g_cmdobj.board,
                    "vul": Vul.from_board(g_cmdobj.board).abbr,
                    "dealer": Player.from_board(g_cmdobj.board).abbr,
                    "curtrick": {
                        player.name: {"suit": c.suit.name, "rank": c.rank.abbr}
                        for player, c in zip(
                            Player.iter_from(g_cmdobj.deal.first),
                            g_cmdobj.deal.curtrick,
                        )
                    },
                    "onlead": g_cmdobj.deal.curplayer.name,
                    "legal_moves": [
                        {"suit": c.suit.name, "rank": c.rank.abbr}
                        for c in g_cmdobj.deal.legal_moves()
                    ],
                },
                "output": output,
                "history": history,
                "history_idx": history_idx,
                "solutions": solutions,
                "ddtable": table,
                "hcp": hcp,
            }
        )

    def get_notfound(self):
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        self.write("404 - Page not found")
