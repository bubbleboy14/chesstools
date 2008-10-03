try:
    import psyco
    psyco.full()
except:
    print "install psyco to make your bot run much faster!"

COLORS = {'white':'black','black':'white'}

import board, move, list, timer, piece, ai, book
from board import Board
from move import Move
from list import List
from timer import Timer, TimeLockTimer