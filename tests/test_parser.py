import unittest
from pathlib import Path
from endplay.parsers import *
from endplay import config
config.use_unicode = False

basedir = Path(__file__).parent


class TestPBN(unittest.TestCase):
	pass

class TestDealer(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.parser = DealerParser()

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
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.parser = LINParser()

	def test_example1(self):
		parser = self.parser
		test_file = basedir / "lin" / "example1.lin"
		with open(test_file) as f:
			res = parser.parse_file(f)
		with open(test_file) as f:
			s = f.read()
			res = parser.parse_string(s)
			

if __name__ == "__main__":
	unittest.main()