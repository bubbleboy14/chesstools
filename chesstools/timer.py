import time

class Timer(object):
    def __init__(self, initial, increment):
        self.players = {}
        self.set(initial, increment)

    def set_clocks(self, p1, p2):
        self.turn = -1
        self.start_time = None
        self.players[-1] = float(p1)
        self.players[1] = float(p2)

    def start(self):
        self.start_time = time.time()

    def stop(self):
        if self.start_time:
            diff = time.time() - self.start_time
            self.start_time = None
            self.players[self.turn] -= diff

    def set(self, initial, increment):
        self.initial = float(initial)
        self.increment = float(increment)
        self.reset()

    def reset(self):
        self.set_clocks(self.initial, self.initial)

    def update(self):
        if self.start_time:
            self.stop()
            self.start()

    def switch(self):
        self.update()
        self.players[self.turn] += self.increment
        self.turn *= -1

    def get_opponent(self, color):
        return self.players[color == 'white' and 1 or -1]

    def get_seconds(self):
        self.update()
        return self.players[-1], self.players[1]

    def get(self):
        secs = list(self.get_seconds())
        times = [[0,0],[0,0]]
        for x in range(2):
            while secs[x] > 59:
                secs[x] -= 60
                times[x][0] += 1
            times[x][1] = str(int(secs[x]))
            if len(times[x][1]) == 1:
                times[x][1] = '0'+times[x][1]
        return ['%s:%s'%tuple(time) for time in times]

class TimeLockTimer(Timer):
    def __init__(self, initial, increment):
        self.players = {}
        self.set(initial, increment)
        self.turn = -1
        self.start_time = None
        self.restore_time = None

    def move_sent(self):
        self.restore_time = time.time()

    def move_received(self):
        if self.restore_time:
            diff = time.time() - self.restore_time
            self.restore_time = None
            self.players[self.turn] += diff
        else:
            print('must call "TimeLockTimer.move_sent()" before "TimeLockTimer.move_received()"')