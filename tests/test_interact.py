import unittest

from endplay.interact.commandobject import CommandObject
from endplay.types import Card, Denom, Player
from endplay.types.deal import Deal


class TestInteractiveDeal(unittest.TestCase):
    def test_properties(self):
        d = Deal(first=Player.south, trump=Denom.spades)
        c = CommandObject(d)
        # first
        c.dispatch(["first", "west"])
        self.assertEqual(c.deal.first, Player.west)
        c.cmd_undo()
        self.assertEqual(c.deal.first, Player.south)

        # trump
        c.cmd_trump(Denom.hearts)
        self.assertEqual(c.deal.trump, Denom.hearts)
        c.cmd_undo()
        self.assertEqual(c.deal.trump, Denom.spades)

    def test_play(self):
        pbn = "N:5... 4... 3... 2..."
        d = Deal(pbn, Player.south, Denom.nt)
        c = CommandObject(d)
        c.cmd_play("S3")
        c.cmd_unplay()
        c.cmd_undo()
        c.cmd_undo()
        self.assertEqual(c.deal.to_pbn(), pbn)
        c.cmd_play("S3")
        c.cmd_play("S2")
        c.cmd_play("S5")
        c.cmd_play("S4")
        self.assertEqual(c.deal.to_pbn(), "N:... ... ... ...")
        c.cmd_undo()
        self.assertEqual(c.deal.east.to_pbn(), "4...")
        self.assertSequenceEqual(c.deal.curtrick, [Card("S3"), Card("S2"), Card("S5")])


if __name__ == "__main__":
    unittest.main()
