import os, re
from sqlalchemy import Table, Column, Integer, String, MetaData, create_engine
from sqlalchemy.orm import mapper, sessionmaker
from chesstools.board import Board
from chesstools.move import Move, to_array, to_algebraic, column_to_index, row_to_index

TYPES = {'P':'Pawn', 'N':'Knight', 'B':'Bishop', 'R':'Rook', 'Q':'Queen', 'K':'King'}
CASTLES = { 'white': {'O-O':'g1','O-O-O':'c1'},
            'black': {'O-O':'g8','O-O-O':'c8'} }

COMMENT = re.compile(r'\{.*\}')
metadata = MetaData()

bookmoves_table = Table('bookmoves', metadata,
    Column('id', Integer, primary_key=True),
    Column('position', String(81)),
    Column('start', String(2)),
    Column('end', String(2)),
    Column('promotion', String(1), default=None),
    Column('strength', Integer, default=1)
)

class BookMove(object):
    def __init__(self, position, start, end, promotion=None, strength=1):
        self.position = position
        self.start = start
        self.end = end
        self.promotion = promotion
        self.strength = strength

    def __repr__(self):
        return '<BookMove %s-%s=%s strength:%s>'%(self.start, self.end, self.promotion, self.strength)

    def __cmp__(self, other):
        return cmp(self.strength, other.strength)

mapper(BookMove, bookmoves_table)

def get_session(db):
    engine = create_engine('sqlite:///%s'%db)
    metadata.bind = engine
    metadata.create_all()
    return sessionmaker(bind=engine, autoflush=True, transactional=True)()

class InvalidBookException(Exception):
    pass

class Book(object):
    def __init__(self, db):
        db += '.book'
        if not os.path.isfile(db): raise InvalidBookException, 'could not find opening book at %s'%db
        self.session = get_session(db)

    def check(self, position):
        moves = self.session.query(BookMove).filter_by(position=position).all()
        moves.sort()
        moves.reverse()
        return [(move.start, move.end, move.promotion) for move in moves]

def process_game(game, session, color):
    board = Board()
    moves = [m for m in game.split(' ') if m and '.' not in m]
    for m in moves:
        position = board.fen_signature()
        if '=' in m:
            promotion = m[-1]
            m = m[:-2]
        else:
            promotion = None
        end = m[-2:]
        if m in ['O-O','O-O-O']:
            pieces = [board.kings[board.turn]]
            end = CASTLES[board.turn][m]
        elif m[0].isupper():
            col, row = None, None
            if len(m) > 3:
                if len(m) == 5: col, row = column_to_index(m[1]), row_to_index(m[2])
                elif m[1].isalpha(): col = column_to_index(m[1])
                else: row = row_to_index(m[1])
            pieces = [p for p in board.pieces(board.turn, col, row, TYPES[m[0]]) if p.legal_move(to_array(end))]
        else:
            pieces = [p for p in board.pawns(board.turn, column_to_index(m[0])) if p.legal_move(to_array(end))]
        if len(pieces) != 1:
            raise Exception, "bad move - %s possibilities for %s: %s"%(len(pieces), m, pieces)
        start = to_algebraic(pieces[0].pos)
        move = Move(start, end, promotion)
        if not color or board.turn == color:
            bookmove = session.query(BookMove).filter_by(position=position, start=move.start, end=move.end, promotion=move.promotion).first()
            if bookmove:
                bookmove.strength += 1
            else:
                session.save(BookMove(position, move.start, move.end, move.promotion))
            session.commit()
        board.move(move)

def process_file(fname, session, color):
    f = open(fname)
    txt = f.read().replace('\n',' ')
    f.close()
    while txt:
        start = txt.find(' 1.')
        if start == -1: break
        txt = txt[start:]
        end = txt.find(' 1-0')
        for ending in [' 0-1',' 1/2-1/2',' *']:
            e = txt.find(ending)
            if end == -1 or e != -1 and e < end:
                end = e
        if end == -1: break
        gtxt, txt = txt[:end], txt[end:]
        comment = COMMENT.search(gtxt)
        while comment:
            gtxt = gtxt[:comment.start()]+gtxt[comment.end():]
            comment = COMMENT.search(gtxt)
        par_open = gtxt.find('(')
        while par_open != -1:
            par_lvl = 1
            par_close = par_open + 1
            while par_close < len(gtxt):
                if gtxt[par_close] == '(':
                    par_lvl += 1
                elif gtxt[par_close] == ')':
                    par_lvl -= 1
                if not par_lvl:
                    break
                par_close += 1
            gtxt = gtxt[:par_open]+gtxt[par_close+1:]
            par_open = gtxt.find('(')
        process_game(gtxt.replace('x','').replace('+','').replace('#','').replace('.','. '), session, color)
    print 'file %s completed'%fname
    if txt:
        print 'leftover text: %s'%txt

def build(pgn, db, color=None):
    if color not in ['white','black']:
        color = None
    db += '.book'
    if os.path.isfile(db) and raw_input('opening book db location exists! add to existing db?\n') != 'yes':
        print 'goodbye'
    else:
        session = get_session(db)
        if os.path.isfile(pgn):
            process_file(pgn, session, color)
        elif os.path.isdir(pgn):
            for f in [x for x in os.walk(pgn).next()[2] if x.endswith('.pgn')]:
                process_file(os.path.join(pgn, f), session, color)
        else:
            print 'source file or directory does not exist!'

def _build_command_line():
    build(raw_input('where is the file or directory of pgn-formatted games?\n'), raw_input('what will you call this opening book database?\n'), raw_input('which color should i use? ("white", "black", or "both")\n'))