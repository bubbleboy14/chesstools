from datetime import datetime
from fyg import config as confyg
from fyg.util import Loggy
from databae.poly import ModelBase
import databae as db

confyg.log.allow.append("db")
db.config.update("prags", "fast")
db.config.update("optimize", True)
db.config.pool.update("null", False)

# TODO : ModelBase->FlatBase ; fixed-length sig

class Transposition(ModelBase):
    sig = db.String(indexed=True)
    score = db.Integer()
    depth = db.Integer()

class Table(Loggy):
    def __init__(self, preppy=True):
        self._all = {}
        self.timers = {}
        self._deepest = {}
        self.preppy = preppy
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

    def query(self, filt, order=None, single=False, timed=True):
        q = Transposition.query(cols=[
            "sig", "depth", "score"
        ]).filter(filt)
        if order is not None:
            q.order(order)
        func = single and q.get or q.all
        if timed:
            return self.timed("query", func)
        return func()

    def prep(self, allsigs, timed=False):
        if not self.preppy:
            return
        sigs = list(filter(lambda s : s not in self._deepest, allsigs))
        if timed:
            start = datetime.now()
        transes = self.query(Transposition.sig.in_(sigs), timed=not timed)
        if timed:
            self.log("prep", len(allsigs), "in", (datetime.now() - start).total_seconds())
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
            trans = self.query(Transposition.sig == sig, -Transposition.depth, True)
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

    def timed(self, name, cb):
        start = datetime.now()
        rval = cb()
        self.timers[name] += (datetime.now() - start).total_seconds()
        return rval

    def start(self):
        self.size = len(self._deepest.keys())
        self.started = datetime.now()
        self.timers["query"] = self.timers["write"] = 0

    def report(self, saved):
        dt = (datetime.now() - self.started).total_seconds()
        r = lambda v : round(v, 3)
        rr = lambda v : r(v / dt)
        t = self.timers
        newsize = len(self._deepest.keys())
        self.log("saved:", saved, "cache:", newsize, "srate:",
            rr(saved), "crate:", rr(newsize - self.size))
        self.log("total:", r(dt), "query:", r(t["query"]), "write:", r(t["write"]))
        if self.preppy:
            self.log("prepped:", self.prepped, "skips:", self.skips, "hits:", self.hits)
            self.prepped = self.skips = self.hits = 0

    def flush(self):
        transes = sum(list(map(self.transets, self._all.keys())), [])
        tlen = len(transes)
        tlen and self.timed("write", lambda : db.put_multi(transes))
        self._all = {}
        self.report(tlen)