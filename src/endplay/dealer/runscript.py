"""
All-purpose routine for executing a dealer script file. This can be
called directly from within Python to convert a dealer file into a 
list of deals, but its main purpose is as the entry point for the
main module.
"""

from __future__ import annotations

from typing import Optional
import shutil
from tempfile import mkdtemp
import time
from subprocess import run
from endplay.parsers.dealer import DealerParser, ParseException, Node
from endplay.dealer.constraint import ConstraintInterpreter
from endplay.dealer.actions import TerminalActions, LaTeXActions, HTMLActions
from endplay.dealer.generate import generate_deals
from endplay.types import Deal
import random

class LaTeXError(RuntimeError):
	"Raised when there was an error running pdflatex"
	pass

def run_script(
	script: Optional[str], 
	show_progress: bool = False,
	produce: int = 40,
	generate: int = 1000000,
	seed: int = None,
	verbose: bool = False,
	swapping: int = 0,
	outformat: str = "plain",
	outfile: Optional[str] = None,
	constraints: list[str] = [],
	actions: list[str] = [],
	predeal: str = "",
	board_numbers: bool = False) -> list[Deal]:
	"""
	Execute a dealer script file

	:param script: The name of the script file to run
	:param show_progress: Display a progress meter while hands are generated
	:param produce: The number of hands to produce
	:param generate: The maximum number of shuffles to perform
	:param seed: The seed for the random number generator
	:param verbose: Print extra debugging info and statistics at completion
	:param swapping: The swapping algorithm to use (0=no swapping, 2=swap EW, 3=all permutations of SEW)
	:param outformat: The format to print output in: 'plain', 'latex' or 'pdf'
	:param outfile: A filename to write the output to, if None then printed to stdout
	:param constraints: A list of extra constraints to apply
	:param actions: A list of extra actions to apply
	:param predeal: A list of players and the suit holdings to deal to them
	:param board_numbers: If True, print board numbers along with the generated deals
	:return: The generated deals in a list
	"""

	start_time = time.time()

	# If we are asked to produce more hands than we generate, we will always fail so let's not
	# waste any time trying
	if produce > generate:
		raise ValueError(f"Asked to produce {produce} hands by generating {generate} hands")

	if seed is None:
		# Generate a seed between 0 and 2**32-1 (required by numpy.random.RandomState)
		# so that if the verbose option is passed we can print out the value of the initial
		# seed at the end of the run
		seed = random.randrange((1 << 32) - 1)

	# Interpret constraints and actions
	parser = DealerParser()
	constraints = [parser.parse_expr(c) for c in constraints]
	actions = [child for a in actions for child in parser.parse_string("action " + a).first_child.children]
	if predeal:
		predeal_node = parser.parse_string("predeal " + predeal)
		deal = predeal_node.first_child.first_child.value
	else:
		deal = Deal()

	# Parse script into document tree
	if script is None:
		doctree = Node("root", Node.ROOT)
	else:
		try:
			with open(script) as f:
				doctree = parser.parse_file(f)
		except FileNotFoundError as e:
			raise RuntimeError(f"{script}: no such file")
		except OSError as e:
			raise RuntimeError(f"Could not load script: {e}")
		except ParseException as e:
			raise RuntimeError(f"Syntax error: {e}")
		except Exception as e:
			raise RuntimeError(f"Unknown exception occurred: {e}")

	# Initialise remaining variables from script
	interp = ConstraintInterpreter()
	vulnerable = None
	player = None
	try:
		for node in doctree.children:
			if node.value == "generate":
				generate = node.first_child.value
			elif node.value == "produce":
				produce = node.first_child.value
			elif node.value == "vulnerable":
				vulnerable = node.first_child.value
			elif node.value == "dealer":
				player = node.first_child.value
			elif node.value == "predeal":
				deal = node.first_child.value
			elif node.value == "pointcount":
				pointcount = [child.value for child in node.children]
				interp.set_env("hcpscale", pointcount)
			elif node.value == "altcount":
				pointcount = [child.value for child in node.children[1:]]
				interp.set_env(f"pt{node.first_child.value}", pointcount)
			elif node.value == "condition":
				constraints += [node.first_child]
			elif node.value == "action":
				actions += [child for child in node.children]
			elif node.value == "define":
				interp.set_env(node.first_child.value, node.last_child)
			else:
				raise RuntimeError("Unknown dealer input:", node.value)
	except NotImplementedError as e:
		exit(f"One of the features you are trying to use is unimplemented: {e}")
	except Exception as e:
		exit(f"Unknown exception occurred: {e}",)

	# Produce hands
	compiled_constraints = [interp.lambdify(c) for c in constraints]
	deals = []
	generator = generate_deals(
		*compiled_constraints, 
		predeal = deal, 
		swapping = swapping, 
		show_progress = show_progress, 
		produce = produce, 
		seed = seed, 
		max_attempts = generate)
	try:
		while True: deals.append(next(generator))
	except StopIteration as e:
		actual_generated = e.value

	# Try and guess the output format
	if outformat is None:
		if isinstance(outfile, str):
			if outfile.endswith(".html") or outfile.endswith(".htm"):
				outformat = "html"
			elif outfile.endswith(".tex"):
				outformat = "latex"
			elif outfile.endswith(".pdf"):
				outformat = "pdf"
			else:
				outformat = "plain"
		else:
			outformat = "plain"

	# Set up the output engine
	if isinstance(outfile, str):
		outfile_name = outfile
		outfile = open(outfile, "w", encoding="utf-8")
	if outformat == "plain":
		actioner = TerminalActions(deals, outfile, board_numbers)
	elif outformat == "latex":
		actioner = LaTeXActions(deals, outfile, board_numbers)
	elif outformat == "pdf":
		if outfile is None:
			raise RuntimeError("Output file must be specified with pdf file format")
		tmpdir = mkdtemp()
		tmpoutfile = open(tmpdir + "/main.tex", "w", encoding="utf-8")
		actioner = LaTeXActions(deals, tmpoutfile, board_numbers)
	elif outformat == "html":
		actioner = HTMLActions(deals, outfile, board_numbers)
	else:
		raise RuntimeError(f"Unknown file format {outformat} specified")
	actioner.write_preamble()

	# Run actions
	if not actions:
		actioner.printall()
	else:
		for action in actions:
			if action.value == "printall":
				actioner.printall()
			elif action.value == "print":
				actioner.print(*[child.value for child in action.children])
			elif action.value == "printew":
				actioner.printew()
			elif action.value == "printpbn":
				actioner.printpbn()
			elif action.value == "printcompact":
				if len(action.children) == 0:
					expr = None
				else:
					expr = interp.lambdify(action.first_child)
				actioner.printcompact(expr)
			elif action.value == "printoneline":
				if len(action.children) == 0:
					expr = None
				else:
					expr = interp.lambdify(action.first_child)
				actioner.printoneline(expr)
			elif action.value == "printes":
				objs = []
				for child in action.children:
					if child.dtype == Node.VALUE:
						objs.append(child.value)
					else:
						objs.append(interp.lambdify(child))
				actioner.printes(*objs)
			elif action.value == "average":
				if len(action.children) == 2:
					s, expr = action.first_child.value, interp.lambdify(action.last_child)
				else:
					s, expr = None, interp.lambdify(action.last_child)
				actioner.average(expr, s)
			elif action.value == "frequency":
				if action.first_child.dtype == Node.VALUE:
					s, args = action.children[0].value, action.children[1:]
				else:
					s, args = None, action.children
				hargs = [interp.lambdify(args[0]), args[1].value, args[2].value]
				if len(args) > 3:
					hargs += [interp.lambdify(args[3]), args[4].value, args[5].value]
					actioner.frequency2d(*hargs, s)
				else:
					actioner.frequency1d(*hargs, s)
			else:
				raise ValueError(f"Unknown action {action.value}")

	# Close the output engine
	actioner.write_postamble()
	if outfile:
		outfile.close()

	if outformat == "pdf":
		tmpoutfile.close()
		proc = run(["pdflatex", "main.tex"], cwd=tmpdir, input=b'', capture_output=True)
		if proc.returncode != 0:
			with open(tmpdir + "/main.log") as f:
				log = f.read()
			with open(tmpdir + "/main.tex") as f:
				tex = f.read()
			raise LaTeXError("LaTeX error:main.log:\n" + log + "\ninput file:\n" + tex)
		shutil.copy2(tmpdir + "/main.pdf", outfile_name)
		try:
			shutil.rmtree(tmpdir)
		except Exception as e:
			warnings.warn(f"Unable to remove temporary directory tree {tmpdir}", ResourceWarning)

	if verbose:
		print("Generated", actual_generated, "hands")
		print("Produced", len(deals), "hands")
		print("Initial random seed", seed)
		print(f"Time needed {time.time()-start_time:.3f}s")

	return deals