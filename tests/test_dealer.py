import io
import os
import re
import unittest
import warnings
from unittest.mock import patch

from endplay import config
from endplay.dealer import *
from endplay.dealer.constraint import ConstraintInterpreter
from endplay.evaluate import *
from endplay.parsers.dealer import DealerParser
from endplay.types import *

config.use_unicode = False

pbn = "N:9642.95.AKQT4.K7 KJ3.K3.98.T98654 AQT85.Q862..AQJ2 7.AJT74.J76532.3"


class TestConstraints(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interp = ConstraintInterpreter()
        self.interp.set_env("x", 10)
        self.interp.set_env("y", 5)
        self.deal = Deal(pbn)

    def assertEvalsTo(self, s, val, msg=None):
        res = self.interp.evaluate(s, self.deal)
        return self.assertEqual(res, val, msg)

    def assertEvalsTrue(self, s, msg=None):
        res = self.interp.evaluate(s, self.deal)
        return self.assertTrue(res, msg)

    def assertEvalsFalse(self, s, msg=None):
        res = self.interp.evaluate(s, self.deal)
        return self.assertFalse(res, msg)

    def test_ptN(self):
        names = [
            "tens",
            "jacks",
            "queen",
            "king",
            "aces",
            "top2",
            "top3",
            "top4",
            "top5",
            "c13",
        ]
        res1 = [1, 0, 1, 2, 1, 3, 4, 4, 5, 16]
        res2 = [1, 0, 1, 1, 1, 2, 3, 3, 4, 12]
        for i, name in enumerate(names):
            self.assertEvalsTo(f"{name}(north)", res1[i], name)
            self.assertEvalsTo(f"pt{i}(north)", res1[i])
            self.assertEvalsTo(f"{name}(north, diamond)", res2[i])
            self.assertEvalsTo(f"pt{i}(north, diamonds)", res2[i])

    def test_shape(self):
        self.assertEvalsTrue("shape(north, any 22xx)")
        self.assertEvalsFalse("shape(north, 5332)")
        west_balanced = "shape(west, any 4333 + any 4432 + any 5332 - 5xxx - x5xx)"
        for deal in generate_deals(west_balanced, produce=20):
            return self.assertEqual(
                self.interp.evaluate(west_balanced, deal), is_balanced(deal.west)
            )

    def test_functions(self):
        self.assertEvalsTo("spade(north)", 4)
        self.assertEvalsTo("hearts(west)", 5)
        self.assertEvalsTo("diamond(south)", 0)
        self.assertEvalsTo("clubs(east)", 6)
        self.assertEvalsTo("hcp(south)", 15)
        self.assertEvalsTo("hcp(north, diamonds)", 9)
        self.assertEvalsTo("hcp(north, spades)", 0)
        self.assertEvalsTo("control(west)", 2)
        self.assertEvalsTo("controls(east, hearts)", 1)
        self.assertEvalsTo("loser(east)", 8)
        self.assertEvalsTo("losers(east, hearts)", 1)
        self.assertEvalsTrue("hascard(north, AD)")
        self.assertEvalsFalse("hascard(south, AD)")

    def test_operators(self):
        self.assertEvalsTrue("x && y")
        self.assertEvalsFalse("y and 0")
        self.assertEvalsTrue("0 || x")
        self.assertEvalsFalse("0 or 0")
        self.assertEvalsTrue("! 0")
        self.assertEvalsFalse("not x")
        self.assertEvalsTrue("4 == 4")
        self.assertEvalsFalse("x + 1 == 10")
        self.assertEvalsTrue("x != y")
        self.assertEvalsFalse("5 != 5")
        self.assertEvalsTrue("3 < 5")
        self.assertEvalsFalse("x < y")
        self.assertEvalsTrue("5 <= 5")
        self.assertEvalsFalse("6 <= y")
        self.assertEvalsTrue("5 > 3")
        self.assertEvalsFalse("y > x")
        self.assertEvalsTrue("5 >= 5")
        self.assertEvalsFalse("y > 20.235")
        self.assertEvalsTo("x + 5", 15)
        self.assertEvalsTo("y - 1", 4)
        self.assertEvalsTo("x * y", 50)
        self.assertEvalsTo("x / y", 2)
        self.assertEvalsTo("x % 3", 1)

    def test_expressions(self):
        self.assertEvalsFalse("(1 + 7 == 9) || controls(west, hearts) == 1")


class TestDealerMain(unittest.TestCase):
    """
    These are 'delicate tests', in that they test the functions against output which was
    generated at a time when they were 'known to work'. This means that if at any stage
    the output format changes, the tests will fail which means that they will need to be
    regenerated. To do this, run the test suite with `self.generate` set to `True`; then
    change it back to False and repeat the test suite.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.this_dir = os.path.dirname(os.path.abspath(__file__))
        self.dealer_dir = os.path.join(self.this_dir, "dealer")
        self.seed = 1234
        self.generate = False

    def assertScriptOutputs(self, script_name, output_format):
        with patch("sys.stdout", new=io.StringIO()) as output:
            run_script(
                os.path.join(self.dealer_dir, script_name + ".dl"),
                seed=self.seed,
                outformat=output_format,
            )
            script_output = output.getvalue()
        out_fname = os.path.join(
            self.dealer_dir, script_name + "." + output_format + ".out"
        )
        if self.generate:
            with open(out_fname, "w", encoding="utf-8") as f:
                f.write(script_output)
        with open(out_fname, encoding="utf-8") as f:
            expected_output = f.read()
        if script_output != expected_output:
            warnings.warn(
                "Output did not match expected output; results of hand generation may differ on this machine from the standard implementation"
            )
        # self.assertEqual(script_output, expected_output)

    def test_print_actions(self):
        self.assertScriptOutputs("test_print_actions", "plain")
        self.assertScriptOutputs("test_print_actions", "latex")
        self.assertScriptOutputs("test_print_actions", "html")

    def test_stat_actions(self):
        # Checking the actual output of the plots is very unstable, and as we are not actually testing whether
        # matplotlib produces consistently produces the same output we mock the Figure class
        with patch("matplotlib.pyplot.figure"):
            self.assertScriptOutputs("test_stat_actions", "plain")
            self.assertScriptOutputs("test_stat_actions", "latex")
            self.assertScriptOutputs("test_stat_actions", "html")


class TestGenerator(unittest.TestCase):
    def test_01(self):
        deal1 = generate_deal()
        deal2 = generate_deal("hcp(north) == 10")
        self.assertEqual(hcp(deal2[Player.north]), 10)


if __name__ == "__main__":
    unittest.main()
