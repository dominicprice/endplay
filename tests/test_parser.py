
import unittest
from pathlib import Path
from endplay.parsers import pbn, lin, json, dealer
from endplay import config
from tempfile import TemporaryFile
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