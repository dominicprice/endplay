import unittest
from endplay.evaluate import *
from endplay.types import *

from endplay import config
config.use_unicode = False

pbn = "N:974.AJ3.63.AK963 K83.K9752.7.8752 AQJ5.T864.KJ94.4 T62.Q.AQT852.QJT"
pbn2 = "N:4.KJ32.842.AQ743 JT987.Q876.AK5.2 AK532.T.JT6.T985 Q6.A954.Q973.KJ6"

class TestEvaluate(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.deal = Deal(pbn)
	def test_hcp(self):
		deal = self.deal
		self.assertEqual(hcp(deal.north), 12)
		self.assertEqual(hcp(deal.east), 6)
		self.assertEqual(hcp(deal.south), 11)
		self.assertEqual(hcp(deal.west), 11)

	def test_top_honours(self):
		deal = self.deal
		self.assertEqual(top_honours(deal.north.spades), 0)
		self.assertEqual(top_honours(deal.east.hearts), 1, str(deal.east.hearts))
		self.assertEqual(top_honours(deal.south.hearts, Rank.R9), 1)
		self.assertEqual(top_honours(deal.west), 5)
		self.assertEqual(top_honours(deal.north, 1), 2)

	def test_losers(self):
		deal = self.deal
		self.assertEqual(losers(deal.north), 8)
		self.assertEqual(losers(deal.east.hearts), 2)
		self.assertEqual(losers(deal.south), 7)
		self.assertEqual(losers(deal.west.diamonds), 1)

	def test_cccc(self):
		# These test cases can be generated by choosing the Random Hand
		# option on http://rpbridge.net/cgi-bin/xhe1.pl and ignoring
		# the Kaplan-Rubens adjustment
		suit = SuitHolding("AQT432")
		self.assertEqual(cccc(suit), 8.45)
		hand1 = Hand("A2.6.J97532.AQ85")
		self.assertEqual(cccc(hand1), 13.8)
		hand2 = Hand("A6.K954.A93.A984")
		self.assertEqual(cccc(hand2), 17)
		hand3 = Hand("73.t84.qt753.kj3")
		self.assertEqual(cccc(hand3), 6.6)

	def test_rule_of_n(self):
		deal = self.deal
		self.assertEqual(rule_of_n(deal.north), 20)
		self.assertEqual(rule_of_n(deal.east), 15)
		self.assertEqual(rule_of_n(deal.south), 19)
		self.assertEqual(rule_of_n(deal.west), 20)


	def test_exact_shape(self):
		deal = self.deal
		

	def test_shape(self):
		deal = self.deal
		self.assertEqual(exact_shape(deal.north), [3,3,2,5])
		self.assertEqual(exact_shape(deal.south), [4,4,4,1])

		self.assertEqual(shape(deal.north), [5,3,3,2])
		self.assertEqual(shape(deal.south), [4,4,4,1])

		self.assertEqual(major_shape(deal.north), [3,3])
		self.assertEqual(major_shape(deal.south), [4,4])

		self.assertEqual(minor_shape(deal.north), [5,2])
		self.assertEqual(minor_shape(deal.south), [4,1])

		self.assertTrue(is_balanced(deal.north))
		self.assertFalse(is_balanced(deal.south))

		self.assertTrue(is_semibalanced(deal.north))
		self.assertFalse(is_semibalanced(deal.south))

		# is_minor_semibalanced

		self.assertTrue(is_single_suited(deal.west))
		self.assertFalse(is_single_suited(deal.south))

		# is_two_suited

		#is_three_suited
		self.assertTrue(is_three_suited(deal.south))
		self.assertFalse(is_three_suited(deal.north))