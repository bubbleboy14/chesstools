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

    def __lt__(self, other):
        return self.score < other.score

    def __gt__(self, other):
        return self.score > other.score

    def __repr__(self):
        return "<Variation %s>"%(self.sig(),)

    def sig(self):
        return "%s %s"%(self.move, self.score)

    def signature(self):
        if not self._sig:
            self._sig = self.board.fen_signature()
        return self._sig

    def move_info(self):
        return self.move.from_to_promotion()
