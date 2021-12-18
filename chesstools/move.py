COLS = 'abcdefgh'

def from_tile(pos):
    return '%s%s'%(COLS[pos[0]], pos[1]+1)

def to_array(pos):
    return (int(pos[1])-1, COLS.index(pos[0]))

def to_algebraic(pos):
    if not pos:
        return '-'
    return '%s%s'%(COLS[pos[1]], pos[0]+1)

def move_from_array(start, end):
    return Move(to_algebraic(start), to_algebraic(end))

def column_to_index(i):
    if i not in COLS:
        raise Exception("%s not a valid column"%i)
    return COLS.index(i)

def row_to_index(i):
    return int(i) - 1

class Move(object):
    def __init__(self, start, end, promotion=None):
        self.promotion = promotion
        self.start, self.end = self.algebraic = start, end
        self.source, self.destination = self.array_pos = to_array(start), to_array(end)
        self.pgn = None
        self.comment = None

    def __eq__(self, m):
        return isinstance(m, Move) and m.algebraic == self.algebraic

    def __ne__(self, m):
        return not self.__eq__(m)

    def __repr__(self):
        return "<Move %s-%s>"%self.algebraic

    def __str__(self):
        s = self.short_algebraic() or self.long_algebraic()
        if self.comment:
            s += ' {%s}'%self.comment
        return s

    def from_to_promotion(self):
        return self.start, self.end, self.promotion

    def long_algebraic(self):
        return '%s-%s%s'%(self.start, self.end, self.promotion and '=%s'%self.promotion or '')

    def short_algebraic(self):
        return self.pgn

    def set_pgn(self, piece, capture, detail=''):
        if piece.name == "Pawn":
            if capture:
                self.pgn = '%sx%s'%(self.start[0], self.end)
            else:
                self.pgn = self.end
            if self.promotion:
                self.pgn += '=%s'%self.promotion
        elif piece.name == "King" and self.source[1] - self.destination[1] == 2:
            self.pgn = 'O-O-O'
        elif piece.name == "King" and self.destination[1] - self.source[1] == 2:
            self.pgn = 'O-O'
        else:
            if capture:
                self.pgn = '%sx%s'%(str(piece).upper(), self.end)
            else:
                self.pgn = '%s%s'%(str(piece).upper(), self.end)
        self.pgn = self.pgn[:1] + detail + self.pgn[1:]