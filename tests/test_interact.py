import unittest

from endplay.interact import InteractiveDeal
from endplay.types import Card, Denom, Player


class TestInteractiveDeal(unittest.TestCase):

    def test_properties(self):
        d = InteractiveDeal(first=Player.south, trump=Denom.spades)
        # first
        d.first = Player.west
        self.assertEqual(d.first, Player.west)
        d.undo()
        self.assertEqual(d.first, Player.south)
        #trump
        d.trump = Denom.hearts
        self.assertEqual(d.trump, Denom.hearts)
        d.undo()
        self.assertEqual(d.trump, Denom.spades)

    def test_play(self):
        pbn = "N:5... 4... 3... 2..."
        d = InteractiveDeal(pbn, Player.south, Denom.nt)
        d.play("S3")
        d.unplay()
        d.undo()
        d.undo()
        self.assertEqual(d.to_pbn(), pbn)
        d.play("S3")
        d.play("S2")
        d.play("S5")
        d.play("S4")
        self.assertEqual(d.to_pbn(), "N:... ... ... ...")
        d.undo()
        self.assertEqual(d.east.to_pbn(), "4...")
        self.assertSequenceEqual(d.curtrick, [Card("S3"), Card("S2"), Card("S5")])


if __name__ == "__main__":
    unittest.main()
