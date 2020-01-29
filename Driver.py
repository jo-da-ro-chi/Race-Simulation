class Driver:
    def __init__(self, jid):
        self.jid = jid
        self.position = 0
        self.velocity = 0
        self.acceleration = 0
        self.laps = 0

    def __repr__(self):
        return "Driver " + str(self.jid) + ", position:" + str(self.position) + ", vel:" + str(self.velocity) + \
               ", lap: " + str(self.laps)

    def __eq__(self, other):
        return self.jid == other.jid

    def move(self, duration):
        self.position += self.velocity * duration + 0.5 * self.acceleration * duration ** 2
        self.velocity += self.acceleration * duration

    def update_laps(self, track_length):
        self.laps = int(self.position // track_length)
