import unittest
from endplay.types import *
from endplay.dds import *

pbn = "N:9642.95.AKQT4.K7 KJ3.K3.98.T98654 AQT85.Q862..AQJ2 7.AJT74.J76532.3"
pbn2 = "N:953.4.KQT3.AJ972 AJ7.K95.A864.KT6 KQT86.AT87.5.Q83 42.QJ632.J972.54"
pbn3 = "N:653.JT32.432.872 A.A9876.JT8.KJT3 JT972.KQ5.965.Q9 KQ84.4.AKQ7.A654"

class TestAnalyse(unittest.TestCase):
	def test_01(self):
		deal1 = Deal(pbn)
		play1 = ["s9", "sk", "sq", "s7", "h3", "hq", "h4", "h9"]
		exp1 = [1,1,1,4,4,3,3,1,1]
		res1 = analyse_play(deal1, play1)
		self.assertSequenceEqual(list(res1), exp1)
		deal2 = Deal(pbn2)
		deal2.trump = Denom.hearts
		play2 = ["ca", "ck", "cq", "c5", "c7", "c6", "c3", "c4", "cj", "ct", "c8", "s4"]
		exp2 = [7,7,6,6,6,7,6,6,6,6,6,6,6]
		res2 = [r for r in analyse_all_plays([deal1, deal2], [play1, play2])]
		self.assertSequenceEqual(list(res2[0]), exp1)
		self.assertSequenceEqual(list(res2[1]), exp2)

class TestPar(unittest.TestCase):
	def test_01(self):
		deal = Deal(pbn)
		parlist = par(deal, Vul.none, Player.north)
		self.assertEqual(parlist.score, 420)
		self.assertSequenceEqual([str(c) for c in parlist], ["4SN=", "4SS="])

class TestSolve(unittest.TestCase):
	pass

class TestDDTable(unittest.TestCase):
	def test_single(self):
		deal = Deal(pbn)
		ddtable = calc_dd_table(deal)
		self.assertEqual(ddtable[Denom.clubs][Player.north], 8)
		self.assertEqual(ddtable[Denom.diamonds][Player.south], 7)
		self.assertEqual(ddtable[Denom.hearts][Player.west], 5)
		self.assertEqual(ddtable[Denom.spades][Player.east], 0)
		self.assertEqual(ddtable[Denom.notrumps][Player.north], 9)

	def test_group(self):
		d1 = Deal(pbn2)
		d2 = Deal(pbn3)
		calc_all_tables([d1, d2], exclude = [Denom.hearts])
if __name__ == "__main__":
	unittest.main()
	