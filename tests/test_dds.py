import unittest

from endplay import config
from endplay.dds import *
from endplay.dds.solve import SolveMode
from endplay.types import *

config.use_unicode = False

pbn = "N:9642.95.AKQT4.K7 KJ3.K3.98.T98654 AQT85.Q862..AQJ2 7.AJT74.J76532.3"
pbn2 = "N:953.4.KQT3.AJ972 AJ7.K95.A864.KT6 KQT86.AT87.5.Q83 42.QJ632.J972.54"
pbn3 = "N:653.JT32.432.872 A.A9876.JT8.KJT3 JT972.KQ5.965.Q9 KQ84.4.AKQ7.A654"
pbn4 = "N:987... K45... AQ2... T63..."


class TestAnalyse(unittest.TestCase):
    def test_01(self):
        deal1 = Deal(pbn)
        play1 = ["s9", "sk", "sq", "s7", "h3", "hq", "h4", "h9"]
        exp1 = [1, 1, 1, 4, 4, 3, 3, 1, 1]
        self.assertEqual(analyse_start(deal1), exp1[0])
        self.assertEqual(analyse_start(deal1, True), 13 - exp1[0])
        res1a = analyse_play(deal1, play1)
        self.assertSequenceEqual(list(res1a), exp1)
        res1b = analyse_play(deal1, play1, True)
        self.assertSequenceEqual(list(res1b), [13 - x for x in exp1])
        deal2 = Deal(pbn2)
        deal2.trump = Denom.hearts
        play2 = ["ca", "ck", "cq", "c5", "c7", "c6", "c3", "c4", "cj", "ct", "c8", "s4"]
        exp2 = [7, 7, 6, 6, 6, 7, 6, 6, 6, 6, 6, 6, 6]
        self.assertSequenceEqual(analyse_all_starts([deal1, deal2]), [exp1[0], exp2[0]])
        res2a = [r for r in analyse_all_plays([deal1, deal2], [play1, play2])]
        self.assertSequenceEqual(list(res2a[0]), exp1)
        self.assertSequenceEqual(list(res2a[1]), exp2)
        res2b = [r for r in analyse_all_plays([deal1, deal2], [play1, play2], True)]
        self.assertSequenceEqual(list(res2b[0]), [13 - x for x in exp1])
        self.assertSequenceEqual(list(res2b[1]), [13 - x for x in exp2])


class TestPar(unittest.TestCase):
    def test_01(self):
        deal = Deal(pbn)
        parlist = par(deal, Vul.none, Player.north)
        self.assertEqual(parlist.score, 420)
        self.assertSequenceEqual([str(c) for c in parlist], ["4SN=", "4SS="])


class TestSolve(unittest.TestCase):
    def test_solve_one(self):
        d = Deal(pbn4, first=Player.west, trump=Denom.spades)
        d.play("S6")
        for _, tricks in solve_board(d):
            self.assertEqual(tricks, 2)

    def test_solve_all(self):
        d = Deal(pbn4, first=Player.west, trump=Denom.spades)
        d.play("S6")

        deals = [d]
        for solution in solve_all_boards(deals):
            for _, tricks in solution:
                self.assertEqual(tricks, 2)

    def test_modes(self):
        d = Deal(pbn2, first=Player.west, trump=Denom.spades)
        d.play("C4")
        res_expected = {
            SolveMode.Default: [
                (Card("CA"), 9),
                (Card("C7"), 9),
                (Card("C2"), 9),
                (Card("C9"), 9),
                (Card("CJ"), 9),
            ],
            SolveMode.OptimalOne: [(Card("CA"), 9)],
            SolveMode.OptimalAll: [
                (Card("CA"), 9),
                (Card("C7"), 9),
                (Card("C2"), 9),
                (Card("C9"), 9),
                (Card("CJ"), 9),
            ],
            SolveMode.LegalOne: [(Card("CA"), 0)],
            SolveMode.LegalAll: [
                (Card("CA"), 0),
                (Card("C7"), 0),
                (Card("C2"), 0),
                (Card("C9"), 0),
                (Card("CJ"), 0),
            ],
            SolveMode.TargetOne: [(Card("CA"), 3)],
            SolveMode.TargetAll: [
                (Card("CA"), 3),
                (Card("C7"), 3),
                (Card("C2"), 3),
                (Card("C9"), 3),
                (Card("CJ"), 3),
            ],
        }

        for mode, expected in res_expected.items():
            sols = solve_board(d, mode, 3)
            self.assertSequenceEqual(
                expected,
                list(sols),
                f"mode {mode.name} produced unexpected results",
            )


class TestDDTable(unittest.TestCase):
    def test_single(self):
        deal = Deal(pbn)
        ddtable = calc_dd_table(deal)
        self.assertEqual(ddtable[Denom.clubs, Player.north], 8)
        self.assertEqual(ddtable[Denom.diamonds, Player.south], 7)
        self.assertEqual(ddtable[Denom.hearts, Player.west], 5)
        self.assertEqual(ddtable[Denom.spades, Player.east], 0)
        self.assertEqual(ddtable[Denom.nt, Player.north], 9)

    def test_group(self):
        d1 = Deal(pbn2)
        d2 = Deal(pbn3)
        t1, t2 = calc_all_tables([d1, d2], exclude=[Denom.hearts])
        self.assertEqual(t1[Denom.clubs, Player.east], 3)
        self.assertEqual(t1[Denom.diamonds, Player.west], 7)
        self.assertEqual(t1[Denom.hearts, Player.south], 0)  # as excluded, else 6
        self.assertEqual(t1[Denom.spades, Player.north], 10)
        self.assertEqual(t2[Denom.nt, Player.south], 1)
        self.assertEqual(t2[Denom.spades, Player.west], 11)
        self.assertEqual(t2[Denom.hearts, Player.east], 0)  # as excluded, else 10
        self.assertEqual(t2[Denom.diamonds, Player.north], 0)


if __name__ == "__main__":
    unittest.main()
