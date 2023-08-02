import unittest

from endplay import config
from endplay.types import *

config.use_unicode = False

pbn = "N:974.AJ3.63.AK963 K83.K9752.7.8752 AQJ5.T864.KJ94.4 T62.Q.AQT852.QJT"
pbn_hands = [
    "974.AJ3.63.AK963",
    "K83.K9752.7.8752",
    "AQJ5.T864.KJ94.4",
    "T62.Q.AQT852.QJT",
]
pbn2 = "N:4.KJ32.842.AQ743 JT987.Q876.AK5.2 AK532.T.JT6.T985 Q6.A954.Q973.KJ6"


class TestDeal(unittest.TestCase):
    def test_trump(self):
        deal = Deal(pbn)
        self.assertEqual(deal.trump, Denom.nt)
        deal.trump = Denom.spades
        self.assertEqual(deal.trump, Denom.spades)

    def test_first(self):
        deal = Deal(pbn)
        self.assertEqual(deal.first, Player.north)
        deal.first = Player.south
        self.assertEqual(deal.first, Player.south)

    def test_curplayer(self):
        deal = Deal(pbn)
        self.assertEqual(deal.curplayer, Player.north)
        deal.play("S9")
        self.assertEqual(deal.curplayer, Player.east)

    def test_legal_moves(self):
        deal = Deal(pbn)
        deal.play("S4")
        expected = [Card("S3"), Card("S8"), Card("SK")]
        self.assertEqual(expected, deal.legal_moves())

    def test_eq(self):
        a = Deal(pbn)
        b = a.copy()
        self.assertEqual(a, b)
        b.first = Player.west
        self.assertNotEqual(a, b)
        self.assertTrue(a.compare(b, True))
        b.first = a.first
        b.trump = Denom.diamonds
        self.assertNotEqual(a, b)
        self.assertTrue(a.compare(b, True))
        b.trump = a.trump
        b.play("S9")
        self.assertNotEqual(a, b)
        self.assertFalse(a.compare(b, True))

    def test_hands(self):
        deal = Deal(pbn)

        for player, hand in deal:
            self.assertEqual(pbn_hands[player], str(hand))

        self.assertEqual(str(deal.north), "974.AJ3.63.AK963")
        deal.north = "K83.K9752.7.8752"  # type: ignore
        self.assertEqual(str(deal.north), "K83.K9752.7.8752")

        self.assertEqual(str(deal.east), "K83.K9752.7.8752")
        deal.east = deal.south
        self.assertEqual(str(deal.east), "AQJ5.T864.KJ94.4")

        self.assertEqual(str(deal.south), "AQJ5.T864.KJ94.4")
        deal.south = deal.west
        self.assertEqual(str(deal.south), "T62.Q.AQT852.QJT")

        self.assertEqual(str(deal.west), "T62.Q.AQT852.QJT")
        deal.west = "974.AJ3.63.AK963"  # type: ignore
        self.assertEqual(str(deal.west), "974.AJ3.63.AK963")

    def test_curtrick(self):
        deal = Deal(pbn)
        self.assertEqual(len(deal.curtrick), 0)

        deal.play("S9")
        self.assertEqual(len(deal.curtrick), 1)
        self.assertEqual(deal.curtrick[0], Card("S9"))
        deal.unplay()
        self.assertTrue("S9" in deal.north)
        self.assertEqual(len(deal.curtrick), 0)
        deal.play(Card("S9"))

        deal.play("SK")
        self.assertEqual(len(deal.curtrick), 2)
        self.assertEqual(deal.curtrick[1], Card("SK"))

        deal.play("SA")
        self.assertEqual(len(deal.curtrick), 3)
        self.assertEqual(deal.curtrick[2], Card("SA"))

        deal.play("ST")
        self.assertEqual(len(deal.curtrick), 0)

        with self.assertRaises(RuntimeError):
            deal.play("DA")
        with self.assertRaises(RuntimeError):
            deal.unplay()
        deal.play("DA", from_hand=False)

    def test_curtrick2(self):
        deal = Deal(
            "N:J84.JT94.KQT.T97 T93.K5.J9653.J82 K65.A73.72.AKQ53 AQ72.Q862.A84.64",
            Player.west,
            Denom.clubs,
        )
        for (
            card
        ) in "\
			C4 CT C2 C3 HJ HK HA H2 \
			CA C6 C7 C8 CK S7 C9 CJ \
			H3 H6 HT H5 DK D3 D2 DA \
			D8 DQ D5 D7 DT DJ C5 D4 \
			H7 HQ H4 D6 SA S4 S3 S5 \
			S2 SJ S9 S6".split():
            deal.play(card)
        self.assertEqual(len(deal.north), 2)

    def test_pbn(self):
        deal1 = Deal(pbn)
        self.assertEqual(deal1.to_pbn(), pbn)

        deal2 = Deal.from_pbn(pbn2)
        self.assertEqual(deal2.to_pbn(), pbn2)

        pbn_with_suits = "S:SA7.H864.DQJT73.CAKQ SQ2.H952.D62.CJT9742 SKT853.HT3.D954.C653 SJ964.HAKQJ7.DAK8.C8"
        deal3 = Deal(pbn_with_suits)  # assert no error

        pbn_no_first = pbn[2:]
        deal4 = Deal(pbn_no_first)  # assert no error
        self.assertEqual(deal1, deal4)

        pbn_too_many_hands = pbn + " " + pbn_no_first
        self.assertRaises(RuntimeError, lambda: Deal(pbn_too_many_hands))

        pbn_void = "N:974.AJ3.63.AK963 - AQJ5.T864.KJ94.4 -"
        deal5 = Deal(pbn_void)
        self.assertEqual(len(deal5.north), 13)
        self.assertEqual(len(deal5.east), 0)
        self.assertEqual(len(deal5.south), 13)
        self.assertEqual(len(deal5.west), 0)

    def test_json(self):
        pass

    def test_clear(self):
        deal = Deal(pbn)
        deal.play("S9")
        deal.clear()
        self.assertEqual(len(deal.curtrick), 0)
        for player in Player:
            self.assertEqual(len(deal[player]), 0)

    def test_contains(self):
        deal = Deal(pbn)
        for card in "S9 SK SA ST".split():
            deal.play(card)
        self.assertTrue("DA" in deal)
        self.assertFalse("SK" in deal)


class TestHand(unittest.TestCase):
    def test_cards(self):
        hand = Hand()
        self.assertTrue(hand.add("S9"))
        self.assertFalse(hand.add(Card("S9")))
        self.assertTrue("S9" in hand)
        self.assertEqual(hand.extend(["DA", Card("HK"), "S9"]), 2)
        self.assertEqual(len(hand), 3)
        self.assertTrue(hand.remove("S9"))
        self.assertFalse(Card("S9") in hand)
        self.assertFalse(hand.remove("S9"))
        hand = Hand.from_pbn(pbn_hands[0])
        self.assertEqual(hand.to_pbn(), pbn_hands[0])
        hand.clear()
        self.assertEqual(len(hand), 0)
        self.assertRaises(RuntimeError, lambda: Hand("974.AJ3.63.AK963."))

    def test_eq(self):
        a = Hand("974.AJ3.63.AK963")
        b = a.copy()
        self.assertEqual(a, b)
        a.remove("S9")
        self.assertNotEqual(a, b)
        a.add("S9")
        self.assertEqual(a, b)

    def test_suits(self):
        hand = Hand(pbn_hands[0])
        suits = pbn_hands[0].split(".")

        for i, suit in enumerate(Denom.suits()):
            self.assertEqual(str(hand[suit]), suits[i])

        self.assertEqual(str(hand.spades), suits[0])
        hand.spades = suits[1]  # type: ignore
        self.assertEqual(str(hand.spades), suits[1])

        self.assertEqual(str(hand.hearts), suits[1])
        hand.hearts = hand.diamonds
        self.assertEqual(str(hand.hearts), suits[2])

        self.assertEqual(str(hand.diamonds), suits[2])
        hand.diamonds = hand.clubs
        self.assertEqual(str(hand.diamonds), suits[3])

        self.assertEqual(str(hand.clubs), suits[3])
        hand.clubs = suits[0]  # type: ignore
        self.assertEqual(str(hand.clubs), suits[0])


class TestSuitHolding(unittest.TestCase):
    def test_cards(self):
        hand = Hand(pbn_hands[0])
        holding = hand.spades

        self.assertEqual(len(holding), 3)
        self.assertTrue("9" in holding)
        self.assertTrue(Rank.R7 in holding)
        self.assertTrue(AlternateRank.R4 in holding)
        self.assertFalse("A" in holding)

        holding.clear()
        self.assertEqual(len(holding), 0)
        self.assertTrue(holding.add("9"))
        self.assertFalse(holding.add(Rank.R9))
        self.assertEqual(holding.extend((AlternateRank.R9, "7", Rank.R4)), 2)
        self.assertTrue(holding.remove("9"))
        self.assertFalse(holding.remove(Rank.R9))

        for c1, c2 in zip(holding, [Rank.R7, Rank.R4]):
            self.assertEqual(c1, c2)

        for c1, c2 in zip(reversed(holding), [Rank.R4, Rank.R7]):
            self.assertEqual(c1, c2)

        self.assertEqual(str(holding), "74")

    def test_eq(self):
        a = SuitHolding("QT974")
        b = a.copy()
        self.assertEqual(a, b)
        b.remove(Rank.RQ)
        self.assertNotEqual(a, b)
        b.add(Rank.RQ)
        self.assertEqual(a, b)


class TestContract(unittest.TestCase):
    def test_properties(self):
        c = Contract("3NTSxx-1")
        self.assertEqual(c.level, 3)
        self.assertEqual(c.denom, Denom.nt)
        self.assertEqual(c.declarer, Player.south)
        self.assertEqual(c.penalty, Penalty.redoubled)
        self.assertEqual(c.result, -1)
        c.level = 6
        self.assertEqual(c.level, 6)
        c.denom = Denom.spades
        self.assertEqual(c.denom, Denom.spades)
        self.assertEqual(str(c), "6SSxx-1")

        d = Contract("7HW=")
        self.assertEqual(d.level, 7)
        self.assertEqual(d.denom, Denom.hearts)
        self.assertEqual(d.declarer, Player.west)
        self.assertEqual(d.penalty, Penalty.passed)
        self.assertEqual(d.result, 0)
        d.declarer = Player.north
        self.assertEqual(d.declarer, Player.north)
        d.penalty = Penalty.doubled
        self.assertEqual(d.penalty, Penalty.doubled)
        self.assertEqual(str(d), "7HNx=")

        e = Contract("1CEx+4")
        self.assertEqual(e.level, 1)
        self.assertEqual(e.denom, Denom.clubs)
        self.assertEqual(e.declarer, Player.east)
        self.assertEqual(e.penalty, Penalty.doubled)
        self.assertEqual(e.result, 4)
        e.result = -2
        self.assertEqual(e.result, -2)
        self.assertEqual(str(e), "1CEx-2")

    def test_scores(self):
        score_nonvul = lambda s: Contract(s).score(Vul.none)
        score_vul = lambda s: Contract(s).score(Vul.both)

        self.assertEqual(score_nonvul("4HN+1"), 450)
        self.assertEqual(score_vul("3DS+1"), 130)
        self.assertEqual(score_vul("3HS+1"), 170)
        self.assertEqual(score_nonvul("2HS-1"), -50)
        self.assertEqual(score_vul("2SNx+1"), 870)
        self.assertEqual(score_nonvul("3DWx-1"), -100)

    def test_copy_eq(self):
        c = Contract("4HW=")
        other = c.copy()
        self.assertEqual(c, other)
        other.denom = Denom.clubs
        self.assertEqual(c.denom, Denom.hearts)
        self.assertNotEqual(c, other)
        other.denom = c.denom


class TestPlayer(unittest.TestCase):
    def test_find(self):
        self.assertEqual(Player.find("north"), Player.north)
        self.assertEqual(Player.find("S"), Player.south)
        self.assertRaises(ValueError, Player.find, "")
        self.assertRaises(ValueError, Player.find, "thisisnotacompassdirection")

    def test_lin(self):
        self.assertEqual(Player.from_lin(1), Player.south)
        self.assertEqual(Player.from_lin(2), Player.west)
        self.assertRaises(ValueError, Player.from_lin, 0)
        self.assertRaises(ValueError, Player.from_lin, 8)
        for i in range(1, 5):
            self.assertEqual(i, Player.from_lin(i).to_lin())

    def test_iter(self):
        self.assertEqual(Player.north.turns_to(Player.south), 2)
        self.assertEqual(Player.east.turns_to(Player.north), 3)
        self.assertEqual(Player.south.turns_to(Player.south), 0)
        self.assertEqual(Player.north.prev(2), Player.south)
        self.assertEqual(Player.east.next(1), Player.south)
        self.assertEqual(Player.west.lho, Player.north)
        self.assertEqual(Player.north.partner, Player.south)
        self.assertEqual(Player.east.rho, Player.north)

    def test_is_vul(self):
        self.assertTrue(Player.north.is_vul(Vul.ns))
        self.assertTrue(Player.south.is_vul(Vul.both))
        self.assertFalse(Player.east.is_vul(Vul.ns))
        self.assertFalse(Player.west.is_vul(Vul.none))
        self.assertTrue(Player.east.is_vul(Vul.ew))


class TestDenom(unittest.TestCase):
    def test_find(self):
        self.assertEqual(Denom.find("D"), Denom.diamonds)
        self.assertEqual(Denom.find("N"), Denom.nt)
        self.assertEqual(Denom.find("♥"), Denom.hearts)
        self.assertRaises(ValueError, Denom.find, "")
        self.assertRaises(ValueError, Denom.find, "thisisnotadenom")

    def test_predicates(self):
        self.assertTrue(Denom.hearts.is_suit())
        self.assertFalse(Denom.nt.is_suit())
        self.assertTrue(Denom.spades.is_major())
        self.assertFalse(Denom.diamonds.is_major())
        self.assertFalse(Denom.hearts.is_minor())
        self.assertTrue(Denom.clubs.is_minor())


class TestPenalty(unittest.TestCase):
    def test_find(self):
        self.assertEqual(Penalty.find("pass"), Penalty.passed)
        self.assertRaises(ValueError, Penalty.find, "thisisnotapenalty")


class TestRank(unittest.TestCase):
    def test_find(self):
        self.assertEqual(Rank.find("3"), Rank.R3)
        self.assertEqual(Rank.find("J"), Rank.RJ)
        self.assertEqual(Rank.find("q"), Rank.RQ)
        self.assertRaises(ValueError, Rank.find, "")
        self.assertRaises(ValueError, Rank.find, "thisisnotarank")

    def test_find_alternate(self):
        self.assertEqual(AlternateRank.find("t"), AlternateRank.RT)
        self.assertEqual(AlternateRank.find("K"), AlternateRank.RK)
        self.assertRaises(ValueError, AlternateRank.find, "")
        self.assertRaises(ValueError, AlternateRank.find, "thisisnotarank")

    def test_convert(self):
        self.assertEqual(Rank.R2.to_alternate(), AlternateRank.R2)
        self.assertEqual(Rank.R5.to_alternate(), AlternateRank.R5)
        self.assertEqual(Rank.RA.to_alternate(), AlternateRank.RA)
        self.assertEqual(AlternateRank.R2.to_standard(), Rank.R2)
        self.assertEqual(AlternateRank.R5.to_standard(), Rank.R5)
        self.assertEqual(AlternateRank.RA.to_standard(), Rank.RA)
        for rank in Rank:
            self.assertEqual(rank, rank.to_alternate().to_standard())


class TestVul(unittest.TestCase):
    def test_find(self):
        self.assertEqual(Vul.find("ew"), Vul.ew)
        self.assertEqual(Vul.find("-"), Vul.none)
        self.assertRaises(ValueError, Vul.find, "thisisnotavul")

    def test_lin(self):
        self.assertEqual(Vul.from_lin("o"), Vul.none)
        self.assertEqual(Vul.from_lin("b"), Vul.both)
        self.assertEqual(Vul.from_lin("n"), Vul.ns)
        self.assertEqual(Vul.from_lin("e"), Vul.ew)
        for v in "obne":
            self.assertEqual(v, Vul.from_lin(v).to_lin())

    def test_board(self):
        self.assertEqual(Vul.from_board(1), Vul.none)
        self.assertEqual(Vul.from_board(13), Vul.both)
        self.assertEqual(Vul.from_board(18), Vul.ns)
        self.assertEqual(Vul.from_board(35), Vul.ew)


if __name__ == "__main__":
    unittest.main()
