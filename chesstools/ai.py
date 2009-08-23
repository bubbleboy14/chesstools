import random
from thread import start_new_thread

INFINITY = float('inf')

class Variation(object):
    def __init__(self, board, move, score=-INFINITY, current=False):
        if current:
            self.board = board
        else:
            self.board = board.copy()
            self.board.move(move)
        self.move = move
        self.score = score
        self._sig = None

    def __neg__(self):
        return Variation(self.board, self.move, -self.score, True)

    def __cmp__(self, other):
        return cmp(self.score, other.score)

    def __repr__(self):
        return "<Variation %s %s>"%(self.move, self.score)

    def signature(self):
        if not self._sig:
            self._sig = self.board.fen_signature()
        return self._sig

    def move_info(self):
        return self.move.from_to_promotion()

class AI(object):
    def __init__(self, depth, move, output=None, book=None, random=None):
        self._depth = depth
        self._move_cb = move
        self._output_cb = output
        self._book = book
        self._random = random or 1
        self._table = {}

    def __call__(self, board):
        def _think():
            branches = self._branches(board)
            if not branches:
                return self._report('i lose!')
            self._report('analyzing %s moves'%(len(branches)))
            for branch in branches:
                self._step(branch, self._depth, -INFINITY, INFINITY)
                self._report('%s:%s'%(branch.move, branch.score))
            branches.sort()
            self._move([branch.move_info() for branch in branches])
        if self._book:
            moves = self._book.check(board.fen_signature())
            if moves:
                return self._move(moves)
        start_new_thread(_think, ())

    def _move(self, moves):
        self._move_cb(*random.choice(moves[:self._random]))

    def _report(self, data):
        if self._output_cb:
            self._output_cb(data)

    def _branches(self, board):
        return [Variation(board, move) for move in board.all_legal_moves()]

    def _score(self, variation, score, depth=INFINITY):
        variation.score = score
        self._table[variation.signature()] = (variation.score, depth)

    def _step(self, variation, depth, alpha, beta):
        sig = variation.signature()
        if sig in self._table and self._table[sig][1] >= depth:
            variation.score = self._table[sig][0]
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
        raise Exception, "evaluate is unimplemented in the base AI class, and must be overridden by a function that returns a number."
