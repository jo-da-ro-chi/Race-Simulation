import time
from spade.agent import Agent
from random import random
from spade.behaviour import FSMBehaviour, State

from Driver import Driver
from Segment import Segment
from spade.message import Message
from spade.template import Template

STATE_DESIRE = "STATE_DESIRE"
STATE_GATHER_INFO = "STATE_GATHER_INFO"
STATE_RACING = "STATE_RACING"
STATE_ENDING = "STATE_ENDING"


class DriverBehaviour(FSMBehaviour):
    async def on_start(self):
        print(f'{self.__class__.__name__}: running')

    async def on_end(self):
        print(f'{self.__class__.__name__}: ending')
        await self.agent.stop()

    def on_available(self, jid, stanza):
        print("[{}] Agent {} is available.".format(self.agent.name, jid.split("@")[0]))

    def on_subscribed(self, jid):
        print("[{}] Agent {} has accepted the subscription.".format(self.agent.name, jid.split("@")[0]))
        print("[{}] Contacts List: {}".format(self.agent.name, self.agent.presence.get_contacts()))

    def on_subscribe(self, jid):
        print("[{}] Agent {} asked for subscription. Let's approve it.".format(self.agent.name, jid.split("@")[0]))
        self.presence.approve(jid)
        self.presence.subscribe(jid)

    async def run(self):
        self.presence.set_available()

        self.presence.on_subscribe = self.on_subscribe
        self.presence.on_subscribed = self.on_subscribed
        self.presence.on_available = self.on_available


class DesireToRaceState(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')

        msg = await self.receive(timeout=180)

        if msg:
            reply = msg.make_reply()
            parsed_msg = msg.body.lower().split(" ")
            if parsed_msg[0] == "racename":
                self.agent.race_name = " ".join(parsed_msg[1:])
                self.agent.desire = (random() < (self.agent.params_map["desire"] or 0))

                if self.agent.desire:
                    reply.body = "{}".format(self.agent.race_name)
                    self.agent.environment_jid = msg.sender
                    await self.send(reply)

                    self.set_next_state(STATE_GATHER_INFO)
                else:
                    self.set_next_state(STATE_ENDING)


class GatherTrackInfoState(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')

        msg = await self.receive(timeout=10)

        if msg:
            parsed_msg = msg.body.lower().split(" ")
            if parsed_msg[0] == "starting" and parsed_msg[1] == self.agent.race_name:
                for segment in parsed_msg[2:]:
                    self.agent.track.append(Segment(float(segment)))
                    self.agent.track[-1].max_velocity = 5 * (self.agent.params_map["courageous"])
                    self.agent.track_length += float(segment)
                self.set_next_state(STATE_RACING)
        else:
            self.set_next_state(STATE_ENDING)


class RacingState(State):
    async def run(self):
        # print(f'{self.__class__.__name__}: running')

        print(self.agent.driver)

        new_acceleration = (1, -1)[self.agent.driver.velocity > self.agent.track[self.agent.position_to_segment()].max_velocity]
        message = Message(to=str(self.agent.environment_jid))
        message.body = "acceleration " + str(new_acceleration)  # TODO adjust acceleration calculation
        await self.send(message)

        # if self.agent.driver.velocity < self.agent.track[self.agent.position_to_segment()].max_velocity:  # TODO add crash impact
        #     message = Message(to=str(self.agent.environment_jid))
        #     message.body = "acceleration 1"  # TODO adjust acceleration calculation
        #     await self.send(message)

        msg = await self.receive(timeout=5)

        if msg:
            parsed_msg = msg.body.lower().split(" ")
            if parsed_msg[0] == "status":
                if self.agent.driver.laps != int(parsed_msg[4]):
                    self.agent.track_update()
                self.agent.driver.position = float(parsed_msg[1])
                self.agent.driver.velocity = float(parsed_msg[2])
                self.agent.driver.acceleration = float(parsed_msg[3])
                self.agent.driver.laps = int(parsed_msg[4])

            if parsed_msg[0] == "accident":
                print("accident occurred!")
                current_segment = self.agent.position_to_segment()

                self.agent.track[current_segment].crash_last = True
                self.agent.track[current_segment].crash_ever = True

        self.set_next_state(STATE_RACING)


class Ending(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')


class DriverAgent(Agent):
    def __init__(self, jid, password, params_map):
        super().__init__(jid, password)
        self.race_name = ""
        self.desire = False
        self.params_map = params_map
        self.track = []
        self.track_length = 0
        self.driver = Driver(jid)
        self.environment_jid = ""

    async def setup(self):
        fsm = DriverBehaviour()
        fsm.add_state(name=STATE_DESIRE, state=DesireToRaceState(), initial=True)
        fsm.add_state(name=STATE_GATHER_INFO, state=GatherTrackInfoState())
        fsm.add_state(name=STATE_RACING, state=RacingState())
        fsm.add_state(name=STATE_ENDING, state=Ending())

        fsm.add_transition(source=STATE_DESIRE, dest=STATE_GATHER_INFO)
        fsm.add_transition(source=STATE_DESIRE, dest=STATE_ENDING)
        fsm.add_transition(source=STATE_GATHER_INFO, dest=STATE_RACING)
        fsm.add_transition(source=STATE_RACING, dest=STATE_RACING)

        self.add_behaviour(fsm)

    def position_to_segment(self):
        distance = 0
        for i, segment in enumerate(self.track):
            distance += segment.length
            if distance > (self.driver.position % self.track_length):
                return i

    def track_update(self):
        for segment in self.track:
            if segment.crash_last:
                segment.max_velocity *= self.params_map["courageous"]
            elif not segment.crash_last and segment.crash_ever:
                segment.max_velocity *= (1 + self.params_map["courageous"])
            else:
                segment.max_velocity *= (1 + 2 * self.params_map["courageous"])
            segment.crash_last = False
