from fyg.util import Loggy
import databae as db

class Transposition(db.ModelBase):
    sig = db.String()
    score = db.Integer()
    depth = db.Integer()

class Table(Loggy):
    def __init__(self):
        self._all = {}
        self._deepest = {}

    def add(self, trans):
        sig = trans.sig
        if sig in self._deepest:
            self._all[sig].append(trans)
            if self._deepest[sig].depth < trans.depth:
                self._deepest[sig] = trans
        else:
            self._deepest[sig] = trans
            self._all[sig] = [trans]

    def get(self, sig, depth):
        if sig in self._deepest:
            deepest = self._deepest[sig]
            if deepest.depth >= depth:
                return deepest
        trans = Transposition.query(Transposition.sig == sig).order(-Transposition.depth).get()
        if trans and trans.depth >= depth:
            return trans

    def score(self, variation, score, depth):
        trans = Transposition()
        trans.depth = depth
        trans.score = variation.score
        trans.sig = variation.signature()
        self.add(trans)

    def flush(self):
        transes = sum(self._all.values(), [])
        self.log("flushing:", len(transes), "cache:", len(self._deepest.keys()))
        db.put_multi(transes)
        self._all = {}