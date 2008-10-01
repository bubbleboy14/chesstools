from chesstools import COLORS
from chesstools.piece import Pawn, Knight, Bishop, Rook, Queen, King
from chesstools.move import to_algebraic

LINEUP = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
PROMOS = {'R':Rook,'N':Knight,'B':Bishop,'Q':Queen}

class Board(object):
    def __init__(self, old_board=None):
        if old_board:
            for key, val in old_board.items():
                setattr(self, key, val)
            for piece in self.pieces():
                piece.board = self
        else:
            self.reset()

    def pawns(self, color=None, column=None, row=None):
        pawns = [p for p in self.pieces(color) if isinstance(p, Pawn)]
        if column is not None:
            pawns = [p for p in pawns if p.column() == column]
        if row is not None:
            pawns = [p for p in pawns if p.row() == row]
        return pawns

    def pieces(self, color=None, column=None, row=None, type=None, pos=None):
        pos = pos or self.position
        pieces = reduce(list.__add__, [[piece for piece in r if piece] for r in pos])
        if color:
            pieces = [p for p in pieces if p.color == color]
        if type:
            pieces = [p for p in pieces if p.name == type]
        if column is not None:
            pieces = [p for p in pieces if p.column() == column]
        if row is not None:
            pieces = [p for p in pieces if p.row() == row]
        return pieces

    def all_focused(self, dest, color=None):
        return [piece for piece in self.pieces(color) if piece.can_target(dest)]

    def all_legal_moves(self):
        return reduce(list.__add__, [piece.all_legal_moves() for piece in self.pieces(self.turn)])

    def all_opponent_moves(self):
        return reduce(list.__add__, [piece.all_legal_moves() for piece in self.pieces(COLORS[self.turn])])

    def copy(self):
        return Board(
            {   'turn':self.turn,
                'kings':self.kings.copy(),
                'en_passant':self.en_passant,
                'fullmove':self.fullmove,
                'halfmove':self.halfmove,
                'all_positions':self.all_positions.copy(),
                'this_position':self.this_position,
                'position':[[p and p.copy() or None for p in row] for row in self.position]
            })

    def reset(self):
        self.turn = 'white'
        self.position = [
            [ LINEUP[i](self, 'white', (0,i)) for i in range(8) ],
            [ Pawn(self, 'white', (1,i)) for i in range(8) ],
            [ None for i in range(8) ],
            [ None for i in range(8) ],
            [ None for i in range(8) ],
            [ None for i in range(8) ],
            [ Pawn(self, 'black', (6,i)) for i in range(8) ],
            [ LINEUP[i](self, 'black', (7,i)) for i in range(8) ]
        ]
        self.kings = { 'white': self.position[0][4],
                       'black': self.position[7][4] }
        self.en_passant = None
        self.fullmove = 1
        self.halfmove = 0
        self.this_position = self.fen_signature()
        self.all_positions = {self.this_position:1}
        self.changes = []
        self.captured = None

    def _fen_layout(self):
        pieces = []
        for row in self.position:
            c = 0
            rstring = ''
            for piece in row:
                if piece:
                    if c:
                        rstring += str(c)
                        c = 0
                    rstring += str(piece)
                else:
                    c += 1
            if c == 8:
                rstring = '8'
            pieces.append(rstring)
        return '/'.join(pieces)

    def _fen_castles(self):
        castles = ''
        if self.kings['white'].castle['king']: castles += 'K'
        if self.kings['white'].castle['queen']: castles += 'Q'
        if self.kings['black'].castle['king']: castles += 'k'
        if self.kings['black'].castle['queen']: castles += 'q'
        return castles

    def fen_signature(self):
        return ' '.join([self._fen_layout(), self.turn[0], self._fen_castles(), to_algebraic(self.en_passant)])

    def fen(self):
        self.position.reverse()
        f = []
        f.append(self._fen_layout()) # piece placement
        f.append(self.turn[0]) # active color
        f.append(self._fen_castles()) # castling
        f.append(to_algebraic(self.en_passant)) # en passant
        f.append(str(self.halfmove)) # halfmove clock
        f.append(str(self.fullmove)) # fullmove clock
        self.position.reverse()
        return ' '.join(f)

    def render(self, pos=None):
        pos = pos or self.position
        pos.reverse()
        b = []
        for row in pos:
            b.append(' '.join([piece and str(piece) or '.' for piece in row]))
        pos.reverse()
        return '\n'.join(b)

    def is_empty(self, p, position=None):
        position = position or self.position
        return not self.get_square(p, position)

    def move_piece(self, a, b, position=None):
        position = position or self.position
        target = self.get_square(a, position)
        if position is self.position:
            target.move(b)
            self.halfmove += 1
            if isinstance(target, Pawn) or self.get_square(b):
                self.halfmove = 0
        self.set_square(b, target, position)
        self.set_square(a, None, position)

    def set_square(self, (r,c), piece, position=None):
        position = position or self.position
        position[r][c] = piece
        if position == self.position:
            self.changes.append(((r,c), piece))

    def get_square(self, (r,c), position=None):
        position = position or self.position
        return position[r][c]

    def is_legal(self, move):
        if move.source == move.destination:
            return False
        source = self.get_square(move.source)
        return source and source.color == self.turn and source.legal_move(move.destination)

    def safe_king(self, source, dest):
        p = self.get_square(source)
        if isinstance(p, King):
            kspot = dest
        else:
            kspot = self.kings[p.color].pos
        return self.safe_square(kspot, p.color, self.make_move(source, dest, True))

    def safe_square(self, dest, color=None, position=None):
        color = color or self.turn
        position = position or self.position
        for piece in self.pieces(COLORS[color], pos=position):
            if piece.can_take(dest, position):
                return False
        return True

    def make_move(self, a, b, test=False, promotion=None):
        if test:
            pos = [[piece for piece in row] for row in self.position]
        else:
            pos = self.position
        target = self.get_square(a)
        self.move_piece(a, b, pos)
        ep = None
        if isinstance(target, Pawn):
            if a[0] - 2 == b[0]:
                ep = (a[0]-1,a[1])
            elif a[0] + 2 == b[0]:
                ep = (a[0]+1,a[1])
            elif self.en_passant == b:
                diff = self.move == 'white' and 1 or -1
                cap_pos = (b[0]+diff,b[1])
                self.captured = self.get_square(cap_pos)
                self.set_square(cap_pos, None, pos)
        elif isinstance(target, King):
            if b[1] - a[1] == 2:
                self.move_piece((a[0], 7), (a[0], 5), pos)
            elif a[1] - b[1] == 2:
                self.move_piece((a[0], 0), (a[0], 3), pos)
        if not test:
            self.en_passant = ep
            if promotion:
                self.set_square(b, PROMOS[promotion](self, self.turn, b))
        return pos

    def not_in_check(self):
        return self.safe_square(self.kings[self.turn].pos)

    def check_position(self):
        return self._mate_or_repetition() or self.halfmove==50 and "50-move rule" or None

    def _mate_or_repetition(self):
        if self.all_positions[self.this_position] == 3:
            return "repetition"
        k = self.kings[self.turn]
        if k.can_move():
            return None
        for piece in self.pieces(self.turn):
            if piece.can_move():
                return None
        if self.safe_square(k.pos):
            return "stalemate"
        else:
            return "checkmate"

    def move(self, move):
        self.changes = []
        piece = self.get_square(move.source)
        self.captured = self.get_square(move.destination)
        detail = ''
        possibilities = [p for p in self.pieces(self.turn) if p is not piece and p.name == piece.name and p.legal_move(move.destination)]
        if possibilities:
            dc, dr = '', ''
            for p in possibilities:
                if p.row() == piece.row(): dc = move.start[0]
                elif p.column() == piece.column(): dr = move.start[1]
            detail = '%s%s'%(dc,dr) or move.start[0]
        move.set_pgn(piece, self.captured, detail)
        self.make_move(move.source, move.destination, promotion=move.promotion)
        self.turn = COLORS[self.turn]
        self.this_position = self.fen_signature()
        if self.this_position not in self.all_positions:
            self.all_positions[self.this_position] = 0
        self.all_positions[self.this_position] += 1
        if self.turn == 'white':
            self.fullmove += 1