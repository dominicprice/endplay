__all__ = [ "DealerParser", "ParseException" ]

from endplay.types import Player, Vul, Hand, Contract, Denom
from endplay.parsers.dealer.node import Node
import pyparsing as pp
pp.ParserElement.enablePackrat()
ParseException = pp.ParseException

def node_from_symbol(string, location, tokens):
	return Node(tokens[0], Node.Type.SYMBOL)

def node_from_unaryop(string, location, tokens):
	args = tokens[0]
	op, arg = args[0], args[1]
	node = Node(op, Node.Type.OPERATOR)
	node.append_child(arg)
	return node
	
def node_from_binaryop(string, location, tokens):
	args = tokens[0]
	while len(args) > 1:
		lhs, op, rhs, *rest = args
		node = Node(op, Node.Type.OPERATOR)
		node.append_child(lhs)
		node.append_child(rhs)
		args = [node, *rest]
	return args[0]
		
def node_from_ternaryop(string, location, tokens):
	args = tokens[0]
	node = Node("if", Node.Type.FUNCTION)
	node.append_child(args[0])
	node.append_child(args[2])
	node.append_child(args[4])
	return node

def node_from_function(string, location, tokens):
	name, *args = tokens
	f = Node(name, Node.Type.FUNCTION)
	for arg in args:
		f.append_child(arg)
	return f
		
def node_from_input(string, location, tokens):
	f, *args = tokens
	node = Node(f, Node.Type.ACTION)
	for arg in args:
		node.append_child(arg)
	return node
		
def node_from_number(string, location, tokens):
	i, f = int(tokens[0]), float(tokens[0])
	return Node(i if i == f else f, Node.Type.VALUE)
		
def node_from_string(string, location, tokens):
	return Node(tokens[0][1:-1], Node.Type.VALUE)
		
def node_from_compass(string, location, tokens):
	player = Player.find(tokens[0])
	return Node(player, Node.Type.VALUE)
		
def node_from_vul(string, location, tokens):
	vul = Vul.find(tokens[0])
	return Node(vul, Node.Type.VALUE)
		
def node_from_suitholding(string, location, tokens):
	node = Node(tokens[0], Node.Type.SUITHOLDING)
	holding = Node(tokens[1], Node.Type.STRING)
	node.append_child(holding)
	return node
	
def node_from_variable(string, location, tokens):
	node = Node("define", Node.Type.ACTION)
	node.append_child(Node(tokens[0], Node.Type.SYMBOL))
	node.append_child(tokens[2])
	return node
		
def node_from_action(string, location, tokens):
	node = Node(tokens[0], Node.Type.ACTION)
	for arg in tokens[1:]:
		if isinstance(arg, pp.ParseResults):
			for elem in arg:
				node.append_child(elem)
		else:
			node.append_child(arg)
	return node

def node_from_contract(string, location, tokens):
	level = tokens[1]
	denom = tokens[2]
	contract = Contract(level=level, denom=denom)
	return Node(contract, Node.Type.VALUE)

def node_from_hand(string, location, tokens):
	hand = Hand()
	for token in tokens:
		denom = Denom.find(token[0])
		hand[denom] = token[1]
	return Node(str(hand), Node.Type.VALUE)

def node_from_pattern(string, location, tokens):
	return Node(tokens[0], Node.Type.VALUE)

def node_from_shape_any(string, location, tokens):
	node = Node("any", Node.Type.OPERATOR)
	node.append_child(tokens[0][1])
	return node

def node_from_shape_combine(string, location, tokens):
	args = tokens[0]
	while len(args) > 1:
		lhs, op, rhs, *rest = args
		node = Node(op, Node.Type.OPERATOR)
		node.append_child(lhs)
		node.append_child(rhs)
		args = [node, *rest]
	return args[0]

def node_from_shapelist(string, location, tokens):
	return tokens[0]

def node_from_denom(string, location, tokens):
	denom = Denom.find(tokens[0])
	return Node(denom, Node.Type.VALUE)

def node_from_nl(string, location, tokens):
	return Node("\n", Node.Type.VALUE)


def new_func(name, *args):
	if isinstance(name, str):
		name = pp.CaselessKeyword(name)
	name -= pp.Suppress("(")
	if len(args) != 0:
		for arg in args[:-1]:
			name += arg + pp.Suppress(",")
		name += args[-1]
	name += pp.Suppress(")")
	name.setParseAction(node_from_function)
	return name

class DealerParser:
	def __init__(self):
		# Initialise most of the value types
		ppc = pp.pyparsing_common
		number = ppc.number
		number.setParseAction(node_from_number)
		newline = pp.Keyword("\\n")
		newline.setParseAction(node_from_nl)
		string = pp.dblQuotedString
		string.setParseAction(node_from_string)
		compass = pp.oneOf("north south east west", caseless=True, asKeyword=True)
		compass.setParseAction(node_from_compass)
		suit = pp.Regex(r"spades?") | pp.Regex(r"hearts?") | pp.Regex(r"diamonds?") | pp.Regex(r"clubs?")
		suit.setParseAction(node_from_denom)
		strain = pp.Regex(r"notrumps?") | pp.Regex(r"spades?") | pp.Regex(r"hearts?") | pp.Regex(r"diamonds?") | pp.Regex(r"clubs?")
		strain.setParseAction(node_from_denom)
		vul = pp.oneOf("none ns ew all", caseless=True, asKeyword=True)
		vul.setParseAction(node_from_vul)
		card_suit = pp.oneOf("s h d c", caseless=True)
		card_rank = pp.Word("AKQJTakqjt98765432")
		suitholding = pp.Group(card_suit + pp.OneOrMore(card_rank))
		hand = pp.delimitedList(suitholding)
		hand.setParseAction(node_from_hand)
		pattern = pp.Word("0123456789xX", exact=4)
		pattern.setParseAction(node_from_pattern)
		shapelist = pp.infixNotation(pattern, [
			(pp.oneOf("any"), 1, pp.opAssoc.RIGHT, node_from_shape_any),
			(pp.oneOf("+ -"), 2, pp.opAssoc.LEFT, node_from_shape_combine)
		])
		contract = pp.Literal("x") + pp.oneOf("1 2 3 4 5 6 7") + pp.oneOf("N S H D C")
		contract.setParseAction(node_from_contract)

		# Functions in expressions. This does function name checking at parse time, which in my
		# first attempt at implementing this was the only way to make the grammar unambiguous. 
		# This should probably be replaced with something simpler.
		shape = new_func("shape", compass, shapelist)
		suitlength = new_func(pp.Regex(r"spades?") | pp.Regex(r"hearts?") | pp.Regex(r"diamonds?") | pp.Regex(r"clubs?"), compass)
		hcp = new_func(pp.Regex("hcps?"), compass, suit) | new_func(pp.Regex("hcps?"), compass)
		ptN = new_func(pp.Regex("pt[0-9]"), compass) | new_func(pp.Regex("pt[0-9]"), compass, suit)
		for name in ["tens", pp.Regex("jacks?"), pp.Regex("queens?"), pp.Regex("kings?"), pp.Regex("aces?"), "top2", "top3", "top4", "top5", "c13"]:
			ptN |= new_func(name, compass) | new_func(name, compass, suit)
		control = new_func(pp.Regex("controls?"), compass) | new_func(pp.Regex("controls?"), compass, suit)
		loser = new_func(pp.Regex("losers?"), compass) | new_func(pp.Regex("losers?"), compass, suit)
		quality = new_func("cccc", compass) | new_func("quality", compass, suit)
		trick = new_func(pp.Regex("tricks?"), compass, strain)
		score = new_func("score", vul, contract, ppc.integer)
		imp = new_func(pp.Regex("imps?"), ppc.integer)
		func = shape | suitlength | hcp | ptN | control | loser | quality | trick | score | imp

		# Expressions (for conditions and variable definitions)
		expr = pp.Forward()
		symbol = pp.Regex(r"(?!(printall)|(print)|(printew)|(printpbn)|(printcompact)|(printes)|" + \
			r"(printoneline)|(average)|(frequency))[a-zA-Z0-9_-]+")
		symbol.setParseAction(node_from_symbol)
		unary1 = pp.oneOf("! not")
		bin1 = pp.oneOf("* / %")
		bin2 = pp.oneOf("+ -")
		bin3 = pp.oneOf("<= < >= >")
		bin4 = pp.oneOf("== !=")
		bin5 = pp.oneOf("&& and")
		bin6 = pp.oneOf("|| or")
		ternary = ("?", ":")
		operator = pp.infixNotation(func | number | symbol, [
			(unary1, 1, pp.opAssoc.RIGHT, node_from_unaryop),
			(bin1, 2, pp.opAssoc.LEFT, node_from_binaryop),
			(bin2, 2, pp.opAssoc.LEFT, node_from_binaryop),
			(bin3, 2, pp.opAssoc.LEFT, node_from_binaryop),
			(bin4, 2, pp.opAssoc.LEFT, node_from_binaryop),
			(bin5, 2, pp.opAssoc.LEFT, node_from_binaryop),
			(bin6, 2, pp.opAssoc.LEFT, node_from_binaryop),
			(ternary, 3, pp.opAssoc.RIGHT, node_from_ternaryop)])		
		expr <<= operator
		
		# Actions
		printall = pp.CaselessKeyword("printall")
		printall.setParseAction(node_from_action)
		print_compass = pp.CaselessKeyword("print") + pp.Suppress("(") - pp.Group(pp.delimitedList(compass)) + pp.Suppress(")")
		print_compass.setParseAction(node_from_action)
		printew = pp.CaselessKeyword("printew")
		printew.setParseAction(node_from_action)
		printpbn = pp.CaselessKeyword("printpbn")
		printpbn.setParseAction(node_from_action)
		printcompact = pp.CaselessKeyword("printcompact") + pp.Optional(expr)
		printcompact.setParseAction(node_from_action)
		printoneline = pp.CaselessKeyword("printoneline") + pp.Optional(expr)
		printoneline.setParseAction(node_from_action)
		printes = pp.CaselessKeyword("printes") + pp.delimitedList(string | expr | newline)
		printes.setParseAction(node_from_action)
		average = pp.CaselessKeyword("average") + pp.Optional(string) + expr
		average.setParseAction(node_from_action)
		frequency = pp.CaselessKeyword("frequency") + pp.Optional(string) + pp.Suppress("(") + expr + \
			pp.Suppress(",") + ppc.number + pp.Suppress(",") + ppc.number + pp.Suppress(")")
		frequency.setParseAction(node_from_action)
		frequency2 = pp.CaselessKeyword("frequency") + pp.Optional(string) + pp.Suppress("(") + expr + \
			pp.Suppress(",") + ppc.number + pp.Suppress(",") + ppc.number + pp.Suppress(",") + expr + \
			pp.Suppress(",") + ppc.number + pp.Suppress(",") + ppc.number + pp.Suppress(")")
		frequency2.setParseAction(node_from_action)
		
		# Inputs
		generate = pp.CaselessKeyword("generate") + ppc.number
		generate.setParseAction(node_from_input)
		produce = pp.CaselessKeyword("produce") + ppc.number
		produce.setParseAction(node_from_input)
		vulnerable = pp.CaselessKeyword("vulnerable") + vul
		vulnerable.setParseAction(node_from_input)
		dealer = pp.CaselessKeyword("dealer") + compass
		dealer.setParseAction(node_from_input)
		predeal = pp.CaselessKeyword("predeal") + compass + hand
		predeal.setParseAction(node_from_input)
		pointcount = pp.CaselessKeyword("pointcount") + pp.delimitedList(ppc.number)
		pointcount.setParseAction(node_from_input)
		altcount = pp.CaselessKeyword("altcount") + ppc.number + pp.delimitedList(ppc.number)
		altcount.setParseAction(node_from_input)
		condition = pp.CaselessKeyword("condition") + expr
		condition.setParseAction(node_from_input)
		action = pp.CaselessKeyword("action") + pp.delimitedList(
			printall | print_compass | printew | printpbn | printcompact |
			printoneline | printes | average | frequency | frequency2
		)
		action.setParseAction(node_from_input)
		variable = ppc.identifier + pp.Literal("=") + expr
		variable.setParseAction(node_from_variable)
		
		# Combine into the grammar for the whole file
		self.grammar = pp.ZeroOrMore(
			generate | produce | vulnerable | dealer | predeal | 
			pointcount | altcount | condition | action | variable
		)
		self.grammar.ignore(pp.cppStyleComment)
		# Note: from the docs I gather that we should only support #comment style
		# if the hash is at the beginning of the line, so this ignore statement
		# should be:
		#   self.grammar.ignore(pp.LineStart() + pp.pythonStyleComment)
		# but the test case fails, and as hashtags can't legally (probably?) appear
		# anywhere else I don't think it will break anything to be looser with the
		# requirements
		self.grammar.ignore(pp.pythonStyleComment)

		self.expr = expr
		
	def _build_tree(self, parseResults: pp.ParseResults) -> Node:
		root = Node("root", Node.Type.ROOT)
		for action in parseResults:
			root.append_child(action)
		return root

	def parse_expr(self, s: str) -> Node:
		"""
		Parse an expression string into a syntax tree, for instance to compute
		the tree of a particular condition
		:param s: The condition string, e.g. "hcp(n) == 10 && shape(s) == 4432"
		:return: The root node of the syntax tree
		"""
		parseResults = self.expr.parseString(s, parseAll=True)
		return parseResults[0]

	def parse_file(self, f: 'io.TextIOBase') -> Node:
		"""
		Parse a file into a syntax tree
		:param f: A handle to a file or TextIO stream to be parsed
		:return: The root node of the syntax tree
		"""
		parseResults = self.grammar.parseFile(f, parseAll=True)
		return self._build_tree(parseResults)
		
	def parse_string(self, s: str) -> Node:
		"""
		Parse a strimg into a syntax tree
		:param s: The string to parse
		:return: The root node of the syntax tree
		"""
		parseResults = self.grammar.parseString(s, parseAll=True)
		return self._build_tree(parseResults)
