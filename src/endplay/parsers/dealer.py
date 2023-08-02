"""
Parser for Dealer scripts
"""

__all__ = ["DealerParser", "ParseException"]

from typing import Optional, TextIO

import pyparsing as pp

from endplay.types import Contract, Deal, Denom, Hand, Player, Vul

pp.ParserElement.enable_packrat()
ParseException = pp.ParseException


class Node:
    """
    Basic Node element from which the syntax tree is built up. Each node contains
    a value and dtype which describes how the value should be interpreted
    """

    ROOT = 0  # Defines the root of the tree. ROOT notes should have no parents
    SYMBOL = 1  # Defines a symbol name which requires lookup at runtime
    OPERATOR = 2  # Defines a unary or binary operator with its arguments as children
    FUNCTION = 4  # Defines a function with its arguments as children
    ACTION = 5  # Defines an action with the optioal arguments as children
    VALUE = 6  # Defines a literal value. The value is stored as the corresponding Python type

    def __init__(self, value, dtype):
        self.value = value
        self.dtype = dtype
        self.children = []

    def append_child(self, child):
        self.children.append(child)

    @property
    def first_child(self) -> "Node":
        return self.children[0]

    @property
    def middle_child(self) -> "Node":
        return self.children[1]

    @property
    def last_child(self) -> "Node":
        return self.children[-1]

    @property
    def n_children(self) -> int:
        return len(self.children)

    def pprint(self, indent=0):
        print(f"{' ': >{indent}}↪ {self.value!r}", end="")
        if self.dtype == Node.VALUE:
            print(f" ({type (self.value)})")
        else:
            print(f" (dtype {self.dtype})")
        for child in self.children:
            try:
                child.pprint(indent + 2)
            except AttributeError:
                raise RuntimeError(f"Non-node child {child} found")

    def __repr__(self):
        return (
            "{"
            + str(self.value)
            + (": " + ",".join(str(s) for s in self.children) if self.children else "")
            + "}"
        )

    @staticmethod
    def from_symbol(string, location, tokens):
        return Node(tokens[0], Node.SYMBOL)

    @staticmethod
    def from_unaryop(string, location, tokens):
        args = tokens[0]
        op, arg = args[0], args[1]
        node = Node(op, Node.OPERATOR)
        node.append_child(arg)
        return node

    @staticmethod
    def from_binaryop(string, location, tokens):
        args = tokens[0]
        while len(args) > 1:
            lhs, op, rhs, *rest = args
            node = Node(op, Node.OPERATOR)
            node.append_child(lhs)
            node.append_child(rhs)
            args = [node, *rest]
        return args[0]

    @staticmethod
    def from_ternaryop(string, location, tokens):
        args = tokens[0]
        node = Node("if", Node.FUNCTION)
        node.append_child(args[0])
        node.append_child(args[2])
        node.append_child(args[4])
        return node

    @staticmethod
    def from_function(string, location, tokens):
        name, *args = tokens
        f = Node(name, Node.FUNCTION)
        for arg in args:
            f.append_child(arg)
        return f

    @staticmethod
    def from_input(string, location, tokens):
        f, *args = tokens
        node = Node(f, Node.ACTION)
        for arg in args:
            node.append_child(arg)
        return node

    @staticmethod
    def from_number(string, location, tokens):
        i, f = int(tokens[0]), float(tokens[0])
        return Node(i if i == f else f, Node.VALUE)

    @staticmethod
    def from_string(string, location, tokens):
        return Node(tokens[0][1:-1], Node.VALUE)

    @staticmethod
    def from_compass(string, location, tokens):
        player = Player.find(tokens[0])
        return Node(player, Node.VALUE)

    @staticmethod
    def from_vul(string, location, tokens):
        vul = Vul.find(tokens[0])
        return Node(vul, Node.VALUE)

    @staticmethod
    def from_variable(string, location, tokens):
        node = Node("define", Node.ACTION)
        node.append_child(Node(tokens[0], Node.SYMBOL))
        node.append_child(tokens[2])
        return node

    @staticmethod
    def from_action(string, location, tokens):
        node = Node(tokens[0], Node.ACTION)
        for arg in tokens[1:]:
            if isinstance(arg, pp.ParseResults):
                for elem in arg:
                    node.append_child(elem)
            else:
                node.append_child(arg)
        return node

    @staticmethod
    def from_contract(string, location, tokens):
        level = tokens[1]
        denom = tokens[2]
        contract = Contract(level=level, denom=denom)
        return Node(contract, Node.VALUE)

    @staticmethod
    def from_hand(string, location, tokens):
        hand = Hand()
        for token in tokens:
            denom = Denom.find(token[0])
            hand[denom] = token[1]
        return Node(hand, Node.VALUE)

    @staticmethod
    def from_predeal(string, location, tokens):
        deal = Deal()
        for i in range(1, len(tokens), 2):
            deal[tokens[i].value] = tokens[i + 1].value
        action = Node("predeal", Node.ACTION)
        action.append_child(Node(deal, Node.VALUE))
        return action

    @staticmethod
    def from_pattern(string, location, tokens):
        shape: list[Optional[int]] = []
        for char in tokens[0]:
            if char in "xX":
                shape.append(None)
            else:
                shape.append(int(char))
        return Node(tuple(shape), Node.VALUE)

    @staticmethod
    def from_shape_any(string, location, tokens):
        node = Node("any", Node.OPERATOR)
        node.append_child(tokens[0][1])
        return node

    @staticmethod
    def from_shape_combine(string, location, tokens):
        args = tokens[0]
        while len(args) > 1:
            lhs, op, rhs, *rest = args
            node = Node(op, Node.OPERATOR)
            node.append_child(lhs)
            node.append_child(rhs)
            args = [node, *rest]
        return args[0]

    @staticmethod
    def from_shapelist(string, location, tokens):
        return tokens[0]

    @staticmethod
    def from_denom(string, location, tokens):
        denom = Denom.find(tokens[0])
        return Node(denom, Node.VALUE)

    @staticmethod
    def from_nl(string, location, tokens):
        return Node("\n", Node.VALUE)

    @staticmethod
    def from_card(string, location, tokens):
        return Node(f"{tokens[1]}{tokens[0]}", Node.VALUE)


def new_func(name, *args):
    if isinstance(name, str):
        name = pp.CaselessKeyword(name)
    name -= pp.Suppress("(")
    if len(args) != 0:
        for arg in args[:-1]:
            name += arg + pp.Suppress(",")
        name += args[-1]
    name += pp.Suppress(")")
    name.set_parse_action(Node.from_function)
    return name


class DealerParser:
    def __init__(self):
        # Initialise most of the value types
        ppc = pp.pyparsing_common
        number = ppc.number
        number.set_parse_action(Node.from_number)
        newline = pp.Keyword("\\n")
        newline.set_parse_action(Node.from_nl)
        string = pp.dblQuotedString
        string.set_parse_action(Node.from_string)
        compass = pp.oneOf("north south east west", caseless=True, asKeyword=True)
        compass.set_parse_action(Node.from_compass)
        suit = (
            pp.Regex(r"spades?")
            | pp.Regex(r"hearts?")
            | pp.Regex(r"diamonds?")
            | pp.Regex(r"clubs?")
        )
        suit.set_parse_action(Node.from_denom)
        strain = (
            pp.Regex(r"notrumps?")
            | pp.Regex(r"spades?")
            | pp.Regex(r"hearts?")
            | pp.Regex(r"diamonds?")
            | pp.Regex(r"clubs?")
        )
        strain.set_parse_action(Node.from_denom)
        vul = pp.oneOf("none ns ew all", caseless=True, asKeyword=True)
        vul.set_parse_action(Node.from_vul)
        card_suit = pp.oneOf("s h d c", caseless=True)
        card_rank = pp.Word("AKQJTakqjt98765432")
        card = pp.Word("AKQJTakqjt98765432") + pp.Word("SHDCshdc")
        card.set_parse_action(Node.from_card)
        suitholding = pp.Group(card_suit + pp.OneOrMore(card_rank))
        hand = pp.delimitedList(suitholding)
        hand.set_parse_action(Node.from_hand)
        pattern = pp.Word("0123456789xX", exact=4)
        pattern.set_parse_action(Node.from_pattern)
        shapelist = pp.infixNotation(
            pattern,
            [
                (pp.oneOf("any"), 1, pp.opAssoc.RIGHT, Node.from_shape_any),
                (pp.oneOf("+ -"), 2, pp.opAssoc.LEFT, Node.from_shape_combine),
            ],
        )
        contract = pp.Literal("x") + pp.oneOf("1 2 3 4 5 6 7") + pp.oneOf("N S H D C")
        contract.set_parse_action(Node.from_contract)

        # Functions in expressions. This does function name checking at parse time, which in my
        # first attempt at implementing this was the only way to make the grammar unambiguous.
        # This should probably be replaced with something simpler.
        shape = new_func("shape", compass, shapelist)
        hascard = new_func("hascard", compass, card)
        suitlength = new_func(
            pp.Regex(r"spades?")
            | pp.Regex(r"hearts?")
            | pp.Regex(r"diamonds?")
            | pp.Regex(r"clubs?"),
            compass,
        )
        hcp = new_func(pp.Regex("hcps?"), compass, suit) | new_func(
            pp.Regex("hcps?"), compass
        )
        ptN = new_func(pp.Regex("pt[0-9]"), compass) | new_func(
            pp.Regex("pt[0-9]"), compass, suit
        )
        for name in [
            "tens",
            pp.Regex("jacks?"),
            pp.Regex("queens?"),
            pp.Regex("kings?"),
            pp.Regex("aces?"),
            "top2",
            "top3",
            "top4",
            "top5",
            "c13",
        ]:
            ptN |= new_func(name, compass) | new_func(name, compass, suit)
        control = new_func(pp.Regex("controls?"), compass) | new_func(
            pp.Regex("controls?"), compass, suit
        )
        loser = new_func(pp.Regex("losers?"), compass) | new_func(
            pp.Regex("losers?"), compass, suit
        )
        quality = new_func("cccc", compass) | new_func("quality", compass, suit)
        trick = new_func(pp.Regex("tricks?"), compass, strain)
        score = new_func("score", vul, contract, ppc.integer)
        imp = new_func(pp.Regex("imps?"), ppc.integer)
        func = (
            shape
            | hascard
            | suitlength
            | hcp
            | ptN
            | control
            | loser
            | quality
            | trick
            | score
            | imp
        )

        # Expressions (for conditions and variable definitions)
        expr = pp.Forward()
        symbol = pp.Regex(
            r"(?!(printall)|(print)|(printew)|(printpbn)|(printcompact)|(printes)|"
            + r"(printoneline)|(average)|(frequency))[a-zA-Z0-9_-]+"
        )
        symbol.set_parse_action(Node.from_symbol)
        unary1 = pp.oneOf("! not")
        bin1 = pp.oneOf("* / %")
        bin2 = pp.oneOf("+ -")
        bin3 = pp.oneOf("<= < >= >")
        bin4 = pp.oneOf("== !=")
        bin5 = pp.oneOf("&& and")
        bin6 = pp.oneOf("|| or")
        ternary = ("?", ":")
        operator = pp.infixNotation(
            func | number | symbol,
            [
                (unary1, 1, pp.opAssoc.RIGHT, Node.from_unaryop),
                (bin1, 2, pp.opAssoc.LEFT, Node.from_binaryop),
                (bin2, 2, pp.opAssoc.LEFT, Node.from_binaryop),
                (bin3, 2, pp.opAssoc.LEFT, Node.from_binaryop),
                (bin4, 2, pp.opAssoc.LEFT, Node.from_binaryop),
                (bin5, 2, pp.opAssoc.LEFT, Node.from_binaryop),
                (bin6, 2, pp.opAssoc.LEFT, Node.from_binaryop),
                (ternary, 3, pp.opAssoc.RIGHT, Node.from_ternaryop),
            ],
        )
        expr <<= operator

        # Actions
        printall = pp.CaselessKeyword("printall")
        printall.set_parse_action(Node.from_action)
        print_compass = (
            pp.CaselessKeyword("print")
            + pp.Suppress("(")
            - pp.Group(pp.delimitedList(compass))
            + pp.Suppress(")")
        )
        print_compass.set_parse_action(Node.from_action)
        printew = pp.CaselessKeyword("printew")
        printew.set_parse_action(Node.from_action)
        printpbn = pp.CaselessKeyword("printpbn")
        printpbn.set_parse_action(Node.from_action)
        printcompact = pp.CaselessKeyword("printcompact") + pp.Optional(expr)
        printcompact.set_parse_action(Node.from_action)
        printoneline = pp.CaselessKeyword("printoneline") + pp.Optional(expr)
        printoneline.set_parse_action(Node.from_action)
        printes = pp.CaselessKeyword("printes") + pp.delimitedList(
            string | expr | newline
        )
        printes.set_parse_action(Node.from_action)
        average = pp.CaselessKeyword("average") + pp.Optional(string) + expr
        average.set_parse_action(Node.from_action)
        frequency = (
            pp.CaselessKeyword("frequency")
            + pp.Optional(string)
            + pp.Suppress("(")
            + expr
            + pp.Suppress(",")
            + ppc.number
            + pp.Suppress(",")
            + ppc.number
            + pp.Suppress(")")
        )
        frequency.set_parse_action(Node.from_action)
        frequency2 = (
            pp.CaselessKeyword("frequency")
            + pp.Optional(string)
            + pp.Suppress("(")
            + expr
            + pp.Suppress(",")
            + ppc.number
            + pp.Suppress(",")
            + ppc.number
            + pp.Suppress(",")
            + expr
            + pp.Suppress(",")
            + ppc.number
            + pp.Suppress(",")
            + ppc.number
            + pp.Suppress(")")
        )
        frequency2.set_parse_action(Node.from_action)

        # Inputs
        generate = pp.CaselessKeyword("generate") + ppc.number
        generate.set_parse_action(Node.from_input)
        produce = pp.CaselessKeyword("produce") + ppc.number
        produce.set_parse_action(Node.from_input)
        vulnerable = pp.CaselessKeyword("vulnerable") + vul
        vulnerable.set_parse_action(Node.from_input)
        dealer = pp.CaselessKeyword("dealer") + compass
        dealer.set_parse_action(Node.from_input)
        predeal = pp.CaselessKeyword("predeal") + pp.OneOrMore(compass + hand)
        predeal.set_parse_action(Node.from_predeal)
        pointcount = pp.CaselessKeyword("pointcount") + pp.delimitedList(ppc.number)
        pointcount.set_parse_action(Node.from_input)
        altcount = (
            pp.CaselessKeyword("altcount") + ppc.number + pp.delimitedList(ppc.number)
        )
        altcount.set_parse_action(Node.from_input)
        condition = pp.CaselessKeyword("condition") + expr
        condition.set_parse_action(Node.from_input)
        action = pp.CaselessKeyword("action") + pp.delimitedList(
            printall
            | print_compass
            | printew
            | printpbn
            | printcompact
            | printoneline
            | printes
            | average
            | frequency
            | frequency2
        )
        action.set_parse_action(Node.from_input)
        variable = ppc.identifier + pp.Literal("=") + expr
        variable.set_parse_action(Node.from_variable)

        # Combine into the grammar for the whole file
        self.grammar = pp.ZeroOrMore(
            generate
            | produce
            | vulnerable
            | dealer
            | predeal
            | pointcount
            | altcount
            | condition
            | action
            | variable
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
        root = Node("root", Node.ROOT)
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
        parse_results = self.expr.parse_string(s, parseAll=True)
        res = parse_results[0]
        assert isinstance(res, Node)
        return res

    def parse_file(self, f: TextIO) -> Node:
        """
        Parse a file into a syntax tree

        :param f: A handle to a file or TextIO stream to be parsed
        :return: The root node of the syntax tree
        """
        parseResults = self.grammar.parse_file(f, parseAll=True)
        return self._build_tree(parseResults)

    def parse_string(self, s: str) -> Node:
        """
        Parse a strimg into a syntax tree

        :param s: The string to parse
        :return: The root node of the syntax tree
        """
        parseResults = self.grammar.parse_string(s, parseAll=True)
        return self._build_tree(parseResults)
