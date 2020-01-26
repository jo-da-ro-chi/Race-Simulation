class Segment:
    def __init__(self, length):
        self.length = length
        self.max_velocity = 0
        self.crash_last = False
        self.crash_ever = False
