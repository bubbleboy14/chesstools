import os, re, time
from sqlalchemy import __version__ as sa_version
from sqlalchemy import Table, Column, Integer, String, MetaData, create_engine
from sqlalchemy.orm import registry, sessionmaker
from chesstools.board import Board
from chesstools.move import Move, to_array, to_algebraic, column_to_index, row_to_index

TYPES = {'P':'Pawn', 'N':'Knight', 'B':'Bishop', 'R':'Rook', 'Q':'Queen', 'K':'King'}
CASTLES = { 'white': {'O-O':'g1','O-O-O':'c1'},
            'black': {'O-O':'g8','O-O-O':'c8'} }
starttime = None

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

    def __lt__(self, other):
        return self.strength < other.strength

    def __cmp__(self, other):
        return cmp(self.strength, other.strength)

registry().map_imperatively(BookMove, bookmoves_table)

def get_session(db):
    engine = create_engine('sqlite:///%s'%db)
    metadata.create_all(engine)
    return sessionmaker(bind=engine)()

class InvalidBookException(Exception):
    pass

class Book(object):
    def __init__(self, db):
        db += '.book'
        if not os.path.isfile(db): raise InvalidBookException('could not find opening book at %s'%db)
        self.session = get_session(db)

    def check(self, position):
        moves = self.session.query(BookMove).filter_by(position=position).all()
        moves.sort()
        moves.reverse()
        return [(move.start, move.end, move.promotion) for move in moves]

def process_game(game, session, color):
    board = Board()
    moves = [m.strip() for m in game.split(' ') if m and '.' not in m]
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
            output('\n******\nerror parsing game\nmove: "%s"\nfen: "%s"\n******'%(m,board.fen()))
            raise Exception("bad move - %s possibilities for %s"%(len(pieces), m))
        start = to_algebraic(pieces[0].pos)
        move = Move(start, end, promotion)
        if color in ['both', board.turn]:
            bookmove = session.query(BookMove).filter_by(position=position, start=move.start, end=move.end, promotion=move.promotion).first()
            if bookmove:
                bookmove.strength += 1
            else:
                session.add(BookMove(position, move.start, move.end, move.promotion))
                session.commit()
        board.move(move)

def process_file(fname, session, color, player):
    output('file %s started'%fname, 1)
    gnum = 0
    f = open(fname)
    txt = f.read().replace('\r','').replace('\n',' ')
    f.close()
    while txt:
        start = txt.find(' 1.')
        if start == -1: break
        headers, txt = txt[:start], txt[start:]
        end = txt.find(' 1-0')
        for ending in [' 0-1',' 1/2-1/2',' *']:
            e = txt.find(ending)
            if end == -1 or e != -1 and e < end:
                end = e
        if end == -1: break
        gtxt, txt = txt[:end], txt[end:]
        if player:
            color = None
            playerheaders = [(h[:5], h[7:h.index('"', 7)]) for h in headers.lower().split('[') if h[:6] in ['white ','black ']]
            for colortag, nametag in playerheaders:
                if player in nametag:
                    if color:
                        color = "both"
                    else:
                        color = colortag
            if not color:
                output('skipping game between %s and %s'%(playerheaders[0][1],playerheaders[1][1]), 3)
                continue
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
        gnum += 1
        if not gnum % 10:
            commit(session, gnum)
    if gnum % 10:
        commit(session, gnum)
    output('file %s completed'%fname, 1)

def commit(session, gnum):
    session.commit()
    output('processed %s games'%(gnum), 2)

def output(data,depth=0):
    print('  '*depth,str(time.time()-starttime)[:6],':',data)

def build(pgn, db, color=None, player=None):
    if float(sa_version[:3]) < 0.5 and input("The chesstools book builder runs EXTREMELY SLOW on SQLAlchemy < 0.5, and you should probably STOP RIGHT NOW and upgrade SQLAlchemy. Are you sure you want to continue?\n") != 'yes':
        return
    global starttime
    starttime = time.time()
    if color != 'player':
        player = None
    db += '.book'
    if os.path.isfile(db) and input('opening book db location exists! add to existing db?\n') != 'yes':
        output('goodbye')
    else:
        output('building database...')
        session = get_session(db)
        if os.path.isfile(pgn):
            process_file(pgn, session, color, player)
        elif os.path.isdir(pgn):
            for f in [x for x in os.walk(pgn).next()[2] if x.endswith('.pgn')]:
                process_file(os.path.join(pgn, f), session, color, player)
        else:
            output('source file or directory does not exist!')

def _build_command_line():
    pgn, db = input('where is the file or directory of pgn-formatted games?\n'), input('\nwhat will you call this opening book database?\n')
    color, player = None, None
    while color not in ['white','black','both','player']:
        color = input('\nwhich color should i use?\n  "white", "black", "both", or "player" (to select player by name)\n')
    if color == 'player':
        player = input('\nok, which player?\n')
    build(pgn, db, color, player)