from fyg import config as confyg
from fyg.util import Loggy
import databae as db

confyg.log.allow.append("db")
db.config.pool.update("null", False)

class Transposition(db.ModelBase):
    sig = db.String()
    score = db.Integer()
    depth = db.Integer()

class Table(Loggy):
    def __init__(self):
        self._all = {}
        self._deepest = {}

    def add(self, sig, dtup, withdb=False):
        if sig not in self._deepest or self._deepest[sig][0] < dtup[0]:
            self._deepest[sig] = dtup
        if withdb:
            if sig not in self._all:
                self._all[sig] = []
            self._all[sig].append(dtup)

    def get(self, sig, depth, withdb=False):
        if sig in self._deepest:
            dtup = self._deepest[sig]
            if dtup[0] >= depth:
                return dtup
        if withdb:
            trans = Transposition.query(Transposition.sig == sig).order(-Transposition.depth).get()
            if trans and trans.depth >= depth:
                return (trans.depth, trans.score)

    def score(self, variation, score, depth, withdb=False):
        self.add(variation.signature(), (depth, score), withdb)

    def trans(self, sig, tup):
        trans = Transposition()
        trans.depth = tup[0]
        trans.score = tup[1]
        trans.sig = sig
        return trans

    def transets(self, sig):
        return list(map(lambda tup : self.trans(sig, tup), self._all[sig]))

    def flush(self):
        transes = sum(list(map(self.transets, self._all.keys())), [])
        db.put_multi(transes)
        self._all = {}
        self.log("saved:", len(transes), "cache:", len(self._deepest.keys()))