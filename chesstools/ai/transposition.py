from fyg.util import Loggy
import databae as db

class Transposition(db.ModelBase):
    sig = db.String()
    score = db.Integer()
    depth = db.Integer()

class Table(Loggy):
    def __init__(self):
        self._table = {}

    def add(self, trans):
        sig = trans.sig
        if sig in self._table:
            rec = self._table[sig]
            rec["all"].append(trans)
            if rec["deepest"].depth < trans.depth:
                rec["deepest"] = trans
        else:
            self._table[sig] = {
                "deepest": trans,
                "all": [trans]
            }

    def get(self, sig, depth):
        if sig in self._table:
            deepest = self._table[sig]["deepest"]
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
        transes = sum([v["all"] for v in self._table.values()], [])
        self.log("flushing", len(transes), "scores")
        db.put_multi(transes)
        self._table = {}