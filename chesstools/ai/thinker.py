from fyg.util import Loggy

INFINITY = float('inf')
PROFILER = None # cProfile or pyinstrument

class Thinker(Loggy):
	def __init__(self, table, depth, stepper, mover, brancher, reporter, rofflim=4, dbuntil=20):
		self.table = table
		self.depth = depth
		self.mover = mover
		self.rofflim = rofflim
		self.dbuntil = dbuntil
		self.stepper = stepper
		self.brancher = brancher
		self.reporter = reporter

	def setBoard(self, board):
		self.board = board
		self.withdb = board.fullmove <= self.dbuntil
		self.branches = self.brancher(board)

	def runoff(self):
		self.branches = self.branches[:self.rofflim]
		self.log("runoff initials:", " vs ".join([b.sig() for b in self.branches]))
		self.depth += 1
		self.evaluate()
		self.depth -= 1
		self.log("runoff rescores:", " vs ".join([b.sig() for b in self.branches]))

	def evaluate(self):
		i = 0
		allhits = True
		blen = len(self.branches)
		self.reporter('scoring %s moves'%(blen,), True)
		for branch in self.branches:
			i += 1
			allhits = self.stepper(branch, self.depth, -INFINITY, INFINITY, self.withdb)
			self.reporter('%s:%s (%s/%s)'%(branch.move, branch.score, i, blen), True)
			self.table.flush()
		self.branches.sort()
		return allhits

	def think(self):
		if not self.branches:
			return self.reporter('i lose!', True)
		if self.evaluate() and len(self.branches) > 1:
			self.log("all hits! calling runoff()")
			self.runoff()
		self.mover([branch.move_info() for branch in self.branches])

	def __call__(self):
		if PROFILER == "cProfile":
			import cProfile
			cProfile.runctx("self.think()", None,
				locals(), "pro/move%s.pro"%(self.board.fullmove,))
		elif PROFILER == "pyinstrument":
			from pyinstrument import Profiler
			with Profiler(interval=0.1) as profiler:
				self.think()
			profiler.print()
		else:
			self.think()
