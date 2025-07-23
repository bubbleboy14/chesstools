__version__ = "0.2.4.1"

try:
    import pyjion
    if input("you have pyjion. it's probs not faster. use it anyway? [N/y] ").lower() == "y":
        pyjion.enable()
        print("pyjioning!!!")
    else:
        print("no pyjion speedup (will probs be faster anyway)")
except:
    try:
        import psyco
        psyco.full()
        print("initializing psyco - wow, you must have python <2.7! how?")
    except:
        print("pyjion (py3.10+) or psyco (py<2.7) _may_ help your bot run faster, but you should really just use pypy")

COLORS = {'white':'black','black':'white'}

from . import board, move, list, timer, piece, ai, book
from .board import Board
from .move import Move
from .list import List
from .timer import Timer, TimeLockTimer
