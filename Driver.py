class Driver:
    def __init__(self, jid):
        self.jid = jid
        self.position = 0
        self.velocity = 0

    def move(self, duration):
        self.position += self.velocity * duration
