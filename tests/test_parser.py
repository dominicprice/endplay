import unittest
from pathlib import Path
from tempfile import TemporaryFile

from endplay import config
from endplay.parsers import dealer, json, lin, pbn
from endplay.types.bid import Bid
from endplay.types.card import Card
from endplay.types.contract import Contract
from endplay.types.player import Player
from endplay.types.vul import Vul

config.use_unicode = False

basedir = Path(__file__).parent


class TestPBN(unittest.TestCase):
    def assertLoadDumpEqual(self, file: Path):
        with open(file) as f:
            boards = pbn.load(f)
        with TemporaryFile("w+") as f2:
            pbn.dump(boards, f2)
            f2.seek(0)
            with open(file) as f1:
                lines1, lines2 = f1.readlines(), f2.readlines()
        self.assertSequenceEqual(lines1, lines2)

    def assertLoadsDumpsEqual(self, file):
        with open(file) as f:
            sin = f.read()
        boards = pbn.loads(sin)
        sout = pbn.dumps(boards)
        self.assertSequenceEqual(sin, sout, seq_type=str)

    def test_01(self):
        file = basedir / "pbn" / "example1.pbn"
        with open(file) as f:
            boards = pbn.load(f)
        self.assertEqual(boards[0].info.event, boards[1].info.event)

    def test_02(self):
        file = basedir / "pbn" / "example2.pbn"
        self.assertLoadsDumpsEqual(file)
        self.assertLoadDumpEqual(file)

    def test_03(self):
        file = basedir / "pbn" / "example3.pbn"
        with open(file) as f:
            boards = pbn.load(f)

    def test_04(self):
        file = basedir / "pbn" / "example4.pbn"
        with open(file) as f:
            boards = pbn.load(f)
        self.assertEqual(len(boards), 1)
        board = boards[0]
        self.assertEqual(board.info.date, "2012.08.??")
        self.assertEqual(board.info.event, "World Championship")
        self.assertEqual(board.info.stage, "Final:1")
        self.assertEqual(board.info.hometeam, "Poland")
        self.assertEqual(board.info.visitteam, "Sweden")
        self.assertEqual(board.info.west, "Nystrom")
        self.assertEqual(board.info.north, "Balicki")
        self.assertEqual(board.info.east, "Upmark")
        self.assertEqual(board.info.south, "Zmudzinski")
        self.assertEqual(board.board_num, 1)
        self.assertEqual(board.dealer, Player.north)
        self.assertEqual(board.vul, Vul.none)
        self.assertEqual(
            board.deal.to_pbn(Player.west),
            "W:.AQJ85.986.JT973 A8643.97642.Q.Q8 KT9.K3.K75.AK652 QJ752.T.AJT432.4",
        )
        self.assertEqual(board.contract, Contract("5CE+1"))
        self.assertSequenceEqual(
            board.auction,
            [
                Bid("1NT"),
                Bid("X"),
                Bid("XX"),
                Bid("4H"),
                Bid("X"),
                Bid("4S"),
                Bid("4NT"),
                Bid("X"),
                Bid("5C"),
                Bid("P"),
                Bid("P"),
                Bid("P"),
            ],
        )
        self.assertSequenceEqual(
            board.play,
            [
                Card("SQ"),
                Card("C3"),
                Card("S3"),
                Card("S9"),
                Card("C7"),
                Card("C8"),
                Card("CK"),
                Card("C4"),
                Card("CQ"),
                Card("CA"),
                Card("D2"),
                Card("C9"),
                Card("HT"),
                Card("H5"),
                Card("H2"),
                Card("HK"),
            ],
        )


class TestDealer(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = dealer.DealerParser()

    def test_example1(self):
        parser = self.parser
        test_file = basedir / "dealer" / "example1.dl"
        with open(test_file) as f:
            res = parser.parse_file(f)
        with open(test_file) as f:
            s = f.read()
            res = parser.parse_string(s)
        # No exception thrown, should be fine right...

    def test_expr(self):
        parser = self.parser
        parser.parse_expr("shape(north, 4432) && hcp(north) == 10")


class TestLIN(unittest.TestCase):
    def assertLoadDumpEqual(self, file: Path):
        with open(file) as f:
            boards = lin.load(f)
        with TemporaryFile("w+") as f2:
            lin.dump(boards, f2)
            f2.seek(0)
            with open(file) as f1:
                lines1, lines2 = f1.readlines(), f2.readlines()
        self.assertSequenceEqual(lines1, lines2)

    def assertLoadsDumpsEqual(self, file):
        with open(file) as f:
            sin = f.read()
        boards = lin.loads(sin)
        sout = lin.dumps(boards)
        self.assertSequenceEqual(sin, sout, seq_type=str)

    def test_01(self):
        file = basedir / "lin" / "example1.lin"
        self.assertLoadsDumpsEqual(file)
        self.assertLoadDumpEqual(file)


class TestJSON(unittest.TestCase):
    def assertPBNLoadsDumps(self, file: Path):
        with open(file) as f:
            sin = f.read()
        boards = pbn.loads(sin)
        jout = json.dumps(boards)
        boards2 = json.loads(jout)
        sout = pbn.dumps(boards2)
        self.assertSequenceEqual(sin, sout, seq_type=str)

    def assertPBNLoadDump(self, file: Path):
        with open(file) as f:
            sin = f.read()
        boards = pbn.loads(sin)
        jout = json.dumps(boards)
        boards2 = json.loads(jout)
        sout = pbn.dumps(boards2)
        self.assertSequenceEqual(sin, sout, seq_type=str)

    def test_01(self):
        file = basedir / "pbn" / "example2.pbn"
        self.assertPBNLoadsDumps(file)


if __name__ == "__main__":
    unittest.main()
