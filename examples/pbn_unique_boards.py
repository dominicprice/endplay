import endplay.parsers.pbn as pbn
from pathlib import Path

if __name__ == "__main__":
	pbn_file = Path("pbn_files", "example1.pbn")
	with open(pbn_file) as f:
		boards = pbn.load(f)

	deals = 