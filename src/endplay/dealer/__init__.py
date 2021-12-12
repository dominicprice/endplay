"""
Functionality for generating bridge deals. This submodule provides an API via
:func:`generate_deals` as well as an executable module which can be run with
`python3 -m endplay.dealer` and which aims to emulate the behaviour of 
Hans van Staveren's original dealer program
"""

__all__ = ['run_script', 'generate_deal', 'generate_deals']

from endplay.dealer.generate import generate_deal, generate_deals
from endplay.dealer.constraint import ConstraintInterpreter
from endplay.dealer.runscript import run_script
