import unittest
from endplay.types import *

from endplay import config
config.use_unicode = False

pbn = "N:974.AJ3.63.AK963 K83.K9752.7.8752 AQJ5.T864.KJ94.4 T62.Q.AQT852.QJT"
pbn_hands = ["974.AJ3.63.AK963", "K83.K9752.7.8752", "AQJ5.T864.KJ94.4", "T62.Q.AQT852.QJT"]
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
		deal.north = "K83.K9752.7.8752"
		self.assertEqual(str(deal.north), "K83.K9752.7.8752")

		self.assertEqual(str(deal.east), "K83.K9752.7.8752")
		deal.east = deal.south
		self.assertEqual(str(deal.east), "AQJ5.T864.KJ94.4")

		self.assertEqual(str(deal.south), "AQJ5.T864.KJ94.4")
		deal.south = deal.west
		self.assertEqual(str(deal.south), "T62.Q.AQT852.QJT")

		self.assertEqual(str(deal.west), "T62.Q.AQT852.QJT")
		deal.west = "974.AJ3.63.AK963"
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
		deal.play("DA", fromHand = False)

	def test_curtrick2(self):
		deal = Deal(
			"N:J84.JT94.KQT.T97 T93.K5.J9653.J82 K65.A73.72.AKQ53 AQ72.Q862.A84.64", 
			Player.west, Denom.clubs)
		for card in "\
			C4 CT C2 C3 HJ HK HA H2 \
			CA C6 C7 C8 CK S7 C9 CJ \
			H3 H6 HT H5 DK D3 D2 DA \
			D8 DQ D5 D7 DT DJ C5 D4 \
			H7 HQ H4 D6 SA S4 S3 S5 \
			S2 SJ S9 S6".split():
			deal.play(card)
		self.assertEqual(len(deal.north), 2)

	def test_pbn(self):
		deal = Deal(pbn)
		self.assertEqual(deal.to_pbn(), pbn)
		deal = Deal.from_pbn(pbn2)
		self.assertEqual(deal.to_pbn(), pbn2)

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
		self.assertEqual(hand.extend(("DA", Card("HK"), "S9")), 2)
		self.assertEqual(len(hand), 3)
		self.assertTrue(hand.remove("S9"))
		self.assertFalse(Card("S9") in hand)
		self.assertFalse(hand.remove("S9"))
		hand = Hand.from_pbn(pbn_hands[0])
		self.assertEqual(hand.to_pbn(), pbn_hands[0])
		hand.clear()
		self.assertEqual(len(hand), 0)

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
		hand.spades = suits[1]
		self.assertEqual(str(hand.spades), suits[1])

		self.assertEqual(str(hand.hearts), suits[1])
		hand.hearts = hand.diamonds
		self.assertEqual(str(hand.hearts), suits[2])

		self.assertEqual(str(hand.diamonds), suits[2])
		hand.diamonds = hand.clubs
		self.assertEqual(str(hand.diamonds), suits[3])

		self.assertEqual(str(hand.clubs), suits[3])
		hand.clubs = suits[0]
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
		other.denom = Denom
		self.assertEqual(c.denom, Denom.spades)
		self.assertNotEqual(c, other)
		other.denom = c.denom
		

class TestCard(unittest.TestCase):
	pass

class TestSuit(unittest.TestCase):
	pass

class TestRank(unittest.TestCase):
	pass

if __name__ == "__main__":
	unittest.main()