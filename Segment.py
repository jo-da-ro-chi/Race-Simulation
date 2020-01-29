class Segment:
    def __init__(self, length):
        self.length = length
        self.max_velocity = 0
        self.crash_last = False
        self.crash_ever = False

    def __repr__(self):
        return "Length: " + str(self.length) + ", max_velocity: " + str(float(self.max_velocity))
