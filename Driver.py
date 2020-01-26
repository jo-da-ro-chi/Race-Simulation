class Driver:
    def __init__(self, jid):
        self.jid = jid
        self.position = 0
        self.velocity = 0
        self.acceleration = 0
        self.laps = 0

    def __repr__(self):
        return "Driver " + str(self.jid) + ", position:" + str(self.position) + ", vel:" + str(self.velocity)

    def move(self, duration):
        self.position += self.velocity * duration + 0.5 * self.acceleration * duration**2
        self.velocity += self.acceleration * duration
