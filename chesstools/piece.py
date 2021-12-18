from chesstools import COLORS
from chesstools.move import Move, to_algebraic, move_from_array
from functools import reduce

MOVES = { "Knight": [[-2,-1],[-1,-2],[2,-1],[1,-2],[-2,1],[-1,2],[2,1],[1,2]],
          "Bishop": [[-1,-1],[-1,1],[1,-1],[1,1]],
          "Rook":   [[0,-1],[0,1],[-1,0],[1,0]] }
MOVES["Queen"] = MOVES["Bishop"] + MOVES["Rook"]

class Piece(object):
    def __init__(self, board, color, pos):
        self.board = board
        self.color = color
        self.pos = pos
        self.name = self.__class__.__name__
        self.init()

    def __str__(self):
        return PIECE_TO_LETTER[self.__class__][self.color]

    def __repr__(self):
        return '<%s %s@%s>'%(self.color, self.name, to_algebraic(self.pos))

    def init(self):
        pass

    def copy(self):
        return self.__class__(None, self.color, self.pos)

    def row(self):
        return self.pos[0]

    def column(self):
        return self.pos[1]

    def _all_moves(self):
        m = []
        for x, y in MOVES[self.name]:
            a, b = self.row(), self.column()
            while True:
                a += x
                b += y
                if a < 0 or b < 0 or a > 7 or b > 7:
                    break
                p = self.board.get_square([a,b])
                if p:
                    if p.color != self.color:
                        m.append([a,b])
                    break
                m.append([a,b])
        return m

    def all_legal_moves(self):
        return [move_from_array(self.pos, move) for move in self._all_moves() if self.board.safe_king(self.pos, move)]

    def legal_move(self, dest):
        return self._good_target(dest) and self._can_move_to(dest) and self._clear_path(self._next_in_path(list(dest))) and self.board.safe_king(self.pos, dest)

    def can_move(self):
        for dest in self._all_moves():
            if self.board.safe_king(self.pos, dest):
                return True
        return False

    def _can_move_to(self, dest):
        return self.can_capture(dest)

    def can_take(self, dest, layout=None):
        return self._enemy_target(dest, layout) and self.can_target(dest, layout)

    def can_target(self, dest, layout=None):
        return self.can_capture(dest, layout) and self._clear_path(self._next_in_path(list(dest)), layout)

    def _enemy_target(self, d, layout=None):
        dest = self.board.get_square(d, layout)
        return dest and dest.color != self.color

    def _good_target(self, d):
        dest = self.board.get_square(d)
        return not dest or dest.color != self.color

    def _clear_path(self, dest, layout=None):
        if tuple(dest) == self.pos:
            return True
        if not self._clear_condition(dest, layout):
            return False
        return self._clear_path(self._next_in_path(dest), layout)

    def _clear_condition(self, dest, layout):
        return self.board.is_empty(dest, layout)

    def _next_in_path(self, dest):
        if dest[0] > self.row(): dest[0] -= 1
        elif dest[0] < self.row(): dest[0] += 1
        if dest[1] > self.column(): dest[1] -= 1
        elif dest[1] < self.column(): dest[1] += 1
        return dest

    def move(self, pos):
        self.pos = pos

class Pawn(Piece):
    def init(self):
        self.direction = self.color == 'white' and 1 or -1
        self.home_row = self.color == 'white' and 1 or 6
        self.promotion_row = self.color == 'white' and 7 or 0

    def _pawn_scan(self, color, cols):
        c = self.column()
        s = 0
        for row in range(1,7):
            for n in cols:
                col = c+n
                if col > 0 and col < 7:
                    p = self.board.get_square((row, col))
                    if p and p.color == color and isinstance(p, Pawn):
                        s += 1
        return s

    def advancement(self):
        if self.color == 'white':
            return self.row()
        else:
            return 7 - self.row()

    def supporting_pawns(self):
        return self._pawn_scan(self.color, [-1,1])

    def opposing_pawns(self):
        return self._pawn_scan(COLORS[self.color], [-1,0,1])

    def all_legal_moves(self):
        m = [move_from_array(self.pos, move) for move in self._all_moves() if self.legal_move(move)]
        if m and self.row() + self.direction == self.promotion_row:
            m = reduce(list.__add__, [[Move(move.start, move.end, letter) for letter in ['q','r','b','n']] for move in m])
        return m

    def _all_moves(self):
        r = self.row()+self.direction
        c = self.column()
        m = [[r, c]]
        if self.row() == self.home_row:
            m.append([r+self.direction, c])
        if c < 7:
            m.append([r, c+1])
        if c > 0:
            m.append([r, c-1])
        return m

    def can_capture(self, dest, layout=None):
        if dest[0] == self.row() + self.direction and abs(dest[1] - self.column()) == 1: # capture
            target = self.board.get_square(dest, layout)
            if target and target.color != self.color: # normal capture
                return True
            if dest == self.board.en_passant: # en passant
                return True
        return False

    def _can_move_to(self, dest):
        if dest[1] == self.column() and self.board.is_empty(dest): # jump
            if dest[0] == self.row() + self.direction: # single
                return True
            elif self.row() == self.home_row and dest[0] == self.row() + 2*self.direction: # double
                return True
        elif self.can_capture(dest):
            return True
        return False

class Knight(Piece):
    def _all_moves(self):
        m = []
        r, c = self.row(), self.column()
        for x, y in MOVES["Knight"]:
            a, b = r+x, c+y
            if a < 0 or b < 0 or a > 7 or b > 7 or not self._good_target([a,b]):
                continue
            m.append([a,b])
        return m

    def can_capture(self, dest, layout=None):
        r = abs(self.row() - dest[0])
        c = abs(self.column() - dest[1])
        if r and c and r + c == 3:
            return True
        return False

    def _clear_path(self, dest, layout=None):
        return True

class Bishop(Piece):
    def can_capture(self, dest, layout=None):
        return abs(self.row() - dest[0]) == abs(self.column() - dest[1])

class Rook(Piece):
    def init(self):
        self.side = None

    def can_capture(self, dest, layout=None):
        return dest[0] == self.row() or dest[1] == self.column()

    def move(self, pos):
        self.pos = pos
        if self.side:
            self.board.kings[self.color].castle[self.side] = None

class Queen(Piece):
    def can_capture(self, dest, layout=None):
        return dest[0] == self.row() or dest[1] == self.column() or abs(self.row() - dest[0]) == abs(self.column() - dest[1])

class King(Piece):
    def init(self):
        self.castle = {'king': None,'queen': None}
        self.home_row = self.color == 'black' and 7 or 0

    def set_castle(self, qr, kr):
        qr.castle_king_column = 2
        kr.castle_king_column = 6
        qr.side = 'queen'
        kr.side = 'king'
        self.castle = {'queen': qr, 'king': kr}

    def copy(self):
        k = King(None, self.color, self.pos)
        k.castle = self.castle.copy()
        return k

    def _all_moves(self):
        m = []
        row, col = self.row(), self.column()
        for x in range(-1,2):
            for y in range(-1,2):
                if x or y:
                    a, b = row+x, col+y
                    if a < 0 or b < 0 or a > 7 or b > 7:
                        continue
                    if self._good_target([a,b]):
                        m.append([a,b])
        if self.board.safe_square(self.pos):
            for rook in list(self.castle.values()):
                if rook:
                    target_square = [row, rook.castle_king_column]
                    # target is empty
                    safemove = self.board.is_empty(target_square)
                    # king and rook are unimpeded
                    if safemove:
                        low = min(col, rook.castle_king_column, rook.column()) + 1
                        high = max(col, rook.castle_king_column, rook.column())
                        for mid_square in [[row, i] for i in range(low, high)]:
                            if not self.board.is_empty(mid_square):
                                safemove = False
                                break
                    # king's path is safe
                    if safemove:
                        low = min(col, rook.castle_king_column) + 1
                        high = max(col, rook.castle_king_column)
                        for mid_square in [[row, i] for i in range(low, high)]:
                            if not self.board.safe_square(mid_square):
                                safemove = False
                                break
                    if safemove:
                        m.append(target_square)
        return m

    def can_capture(self, dest, layout=None):
        return abs(self.row() - dest[0]) < 2 and abs(self.column() - dest[1]) < 2

    def _can_move_to(self, dest):
        if self.can_capture(dest): # normal move
            return True
        if self.board.safe_square(self.pos) and dest[0] == self.home_row: # castle
            for c in list(self.castle.values()):
                if c and dest[1] == c.castle_king_column:
                    return True
        return False

    def _clear_condition(self, dest, layout):
        return self.board.is_empty(dest) and self.board.safe_king(self.pos, dest)

    def move(self, pos):
        self.pos = pos
        self.castle['king'] = None
        self.castle['queen'] = None

# this is mostly here so we can get at these
# strings without having initialized a piece.
PIECE_TO_LETTER = {
    King:   {"white": "K", "black": "k"},
    Queen:  {"white": "Q", "black": "q"},
    Rook:   {"white": "R", "black": "r"},
    Bishop: {"white": "B", "black": "b"},
    Knight: {"white": "N", "black": "n"},
    Pawn:   {"white": "P", "black": "p"}
}

# to help us go the other way
LETTER_TO_PIECE = {
    "K": King,
    "Q": Queen,
    "R": Rook,
    "B": Bishop,
    "N": Knight,
    "P": Pawn
}
