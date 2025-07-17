from fyg.util import Loggy
from _thread import start_new_thread
from random import choice as ranchoice
from .variation import Variation
from .transposition import Table

INFINITY = float('inf')
PROFILER = None # cProfile or pyinstrument

class AI(Loggy):
    def __init__(self, depth, move, output=None, book=None, random=None):
        self._depth = depth
        self._move_cb = move
        self._output_cb = output
        self._book = book
        self._random = random or 1
        self._table = Table()

    def __call__(self, board):
        def _think():
            branches = self._branches(board)
            blen = len(branches)
            if not branches:
                return self._report('i lose!', True)
            self._report('scoring %s moves'%(blen,), True)
            i = 0
            for branch in branches:
                i += 1
                self._step(branch, self._depth, -INFINITY, INFINITY)
                self._report('%s:%s (%s/%s)'%(branch.move, branch.score, i, blen), True)
                self._table.flush()
            branches.sort()
            self._move([branch.move_info() for branch in branches])
        def _dothink():
            if PROFILER == "cProfile":
                import cProfile
                cProfile.runctx("_think()", None,
                    locals(), "pro/move%s.pro"%(board.fullmove,))
            elif PROFILER == "pyinstrument":
                from pyinstrument import Profiler
                with Profiler(interval=0.1) as profiler:
                    _think()
                profiler.print()
            else:
                _think()
        if self._book:
            moves = self._book.check(board.fen_signature())
            if moves:
                return self._move(moves)
        start_new_thread(_dothink, ())

    def _move(self, moves):
        self._move_cb(*ranchoice(moves[:self._random]))

    def _report(self, data, loud=False):
        if self._output_cb:
            self._output_cb(data)
        if loud:
            self.log(data)

    def _branches(self, board):
        return [Variation(board, move) for move in board.all_legal_moves()]

    def _score(self, variation, score, depth=INFINITY):
        variation.score = score
        self._table.score(variation, score, depth)

    def _step(self, variation, depth, alpha, beta):
        sig = variation.signature()
        dtup = self._table.get(sig, depth)
        if dtup:
            variation.score = dtup[1]
            return
        if not depth:
            return self._score(variation, self.evaluate(variation.board), 0)
        branches = self._branches(variation.board)
        if not branches:
            return self._score(variation, -INFINITY)
        for branch in branches:
            self._step(branch, depth-1, -beta, -alpha)
            alpha = max(alpha, -branch.score)
            if alpha >= beta: break
        self._score(variation, alpha, depth)

    def evaluate(self, board):
        raise Exception("evaluate is unimplemented in the base AI class, and must be overridden by a function that returns a number.")