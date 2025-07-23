from fyg.util import Loggy
from _thread import start_new_thread
from random import choice as ranchoice
from .transposition import Table
from .variation import Variation
from .thinker import Thinker

INFINITY = float('inf')

class AI(Loggy):
    def __init__(self, depth, move, output=None, book=None, random=None, runoff=4, dbuntil=20):
        self._depth = depth
        self._move_cb = move
        self._output_cb = output
        self._book = book
        self._random = random or 1
        self._table = Table()
        self._thinker = Thinker(self._table, self._depth,
            self._step, self._move, self._branches, self._report, runoff, dbuntil)

    def __call__(self, board):
        if self._book:
            moves = self._book.check(board.fen_signature())
            if moves:
                return self._move(moves)
        self._thinker.setBoard(board)
        start_new_thread(self._thinker, ())

    def _branches(self, board):
        return [Variation(board, move) for move in board.all_legal_moves()]

    def _move(self, moves):
        self._move_cb(*ranchoice(moves[:self._random]))

    def _report(self, data, loud=False):
        if self._output_cb:
            self._output_cb(data)
        if loud:
            self.log(data)

    def _score(self, variation, score, depth=INFINITY, withdb=False):
        variation.score = score
        self._table.score(variation, score, depth, withdb)

    def _step(self, variation, depth, alpha, beta, withdb=False):
        sig = variation.signature()
        dtup = self._table.get(sig, depth, depth and withdb)
        if dtup:
            variation.score = dtup[1]
            return True
        if not depth:
            return self._score(variation, self.evaluate(variation.board), 0)
        branches = self._branches(variation.board)
        if not branches:
            return self._score(variation, -INFINITY, withdb=withdb)
        for branch in branches:
            self._step(branch, depth-1, -beta, -alpha, withdb)
            alpha = max(alpha, -branch.score)
            if alpha >= beta: break
        self._score(variation, alpha, depth, withdb)

    def evaluate(self, board):
        raise Exception("evaluate is unimplemented in the base AI class, and must be overridden by a function that returns a number.")