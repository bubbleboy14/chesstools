INFINITY = float('inf')
PROFILER = None # cProfile or pyinstrument

class Thinker(object):
	def __init__(self, table, depth, stepper, mover, brancher, reporter):
		self.table = table
		self.depth = depth
		self.mover = mover
		self.stepper = stepper
		self.brancher = brancher
		self.reporter = reporter

	def setBoard(self, board):
		self.board = board
		self.withdb = board.fullmove < 21
		self.branches = self.brancher(board)

	def think(self):
		blen = len(self.branches)
		if not self.branches:
			return self.reporter('i lose!', True)
		self.reporter('scoring %s moves'%(blen,), True)
		i = 0
		for branch in self.branches:
			i += 1
			self.stepper(branch, self.depth, -INFINITY, INFINITY, self.withdb)
			self.reporter('%s:%s (%s/%s)'%(branch.move, branch.score, i, blen), True)
			self.table.flush()
		self.branches.sort()
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
