from datetime import datetime
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
    def __init__(self, preppy=True):
        self.preppy = preppy
        self._all = {}
        self._deepest = {}
        self.prepped = 0
        self.skips = 0
        self.hits = 0

    def add(self, sig, dstup, withdb=False):
        if sig not in self._deepest or self._deepest[sig][0] < dstup[0]:
            self._deepest[sig] = dstup
        if withdb:
            if sig not in self._all:
                self._all[sig] = []
            self._all[sig].append(dstup)

    def query(self, filt):
        return Transposition.query(cols=[
            "sig", "depth", "score"
        ]).filter(filt)

    def prep(self, allsigs):
        if not self.preppy:
            return
        sigs = list(filter(lambda s : s not in self._deepest, allsigs))
        transes = self.query(Transposition.sig.in_(sigs)).all()
        slen = len(sigs)
        self.prepped += slen
        self.hits += len(transes)
        self.skips += len(allsigs) - slen
        for trans in transes:
            self.add(trans[0], (trans[1], trans[2]))

    def get(self, sig, depth, withdb=False):
        if sig in self._deepest:
            dstup = self._deepest[sig]
            if dstup[0] >= depth:
                return dstup
        if withdb and not self.preppy:
            trans = self.query(Transposition.sig == sig).order(-Transposition.depth).get()
            if trans and trans[1] >= depth:
                return (trans[1], trans[2])

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

    def start(self):
        self.started = datetime.now()
        self.size = len(self._deepest.keys())

    def report(self, saved):
        dt = (datetime.now() - self.started).total_seconds()
        newsize = len(self._deepest.keys())
        self.log("saved:", saved, "cache:", newsize, "time:", dt)
        self.log("srate:", round(saved / dt, 3), "crate:", round((newsize - self.size) / dt, 3))
        if self.preppy:
            self.log("prepped:", self.prepped, "skips:", self.skips, "hits:", self.hits)
            self.prepped = self.skips = self.hits = 0

    def flush(self):
        transes = sum(list(map(self.transets, self._all.keys())), [])
        db.put_multi(transes)
        self._all = {}
        self.report(len(transes))