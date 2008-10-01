import os, datetime
from chesstools import COLORS

class List(object):
    def __init__(self):
        self.reset()

    def __str__(self):
        return '\n'.join(self.all())

    def reset(self, tc=(0,0), white=None, black=None):
        self.moves = []
        self.last_move = None
        self.outcome = None
        self.tc = tc
        self.white = white
        self.black = black

    def all(self, breaks=False):
        m = []
        c = 0
        for i, (w,b) in enumerate(self.moves):
            line = "%s. %s %s"%(i+1, w, b or '')
            m.append(line)
            if breaks:
                c += len(line)
                if c > 70:
                    m.append('\n')
                    c = 0
        m.append(self.outcome or '*')
        return m

    def add(self, move):
        self.last_move = move
        if not self.moves or self.moves[-1][1]:
            self.moves.append([move, None])
        else:
            self.moves[-1][1] = move

    def save(self, side='white'):
        p = 'saves'
        date = str(datetime.datetime.now().date()).replace('-','.')
        for d in [getattr(self, side), getattr(self, COLORS[side]), date]:
            p = os.path.join(p, d)
            if not os.path.isdir(p):
                os.mkdir(p)
        c = len(os.walk(p).next()[2]) + 1
        f = open(os.path.join(p,'%s.pgn'%c),'w')
        f.write('[Event "%s-%s game"]\n'%self.tc)
        f.write('[Site "MICS"]\n')
        f.write('[Date "%s"]\n'%date)
        f.write('[Round ""]\n')
        f.write('[White "%s"]\n'%self.white)
        f.write('[Black "%s"]\n'%self.black)
        f.write('[Result "%s"]\n\n'%(self.outcome or '*'))
        f.write(' '.join(self.all(True)))
        f.close()