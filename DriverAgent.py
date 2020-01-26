import time
from spade.agent import Agent
from random import random
from spade.behaviour import FSMBehaviour, State
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

        msg = await self.receive(timeout=10)

        if msg:
            reply = msg.make_reply()
            parsed_msg = msg.body.lower().split(" ")
            if parsed_msg[0] == "racename":
                self.agent.race_name = " ".join(parsed_msg[1:])
                self.agent.desire = (random() < (self.agent.params_map["desire"] or 0))

                if self.agent.desire:
                    reply.body = "{}".format(self.agent.race_name)
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
                    
                self.set_next_state(STATE_RACING)
        else:
            self.set_next_state(STATE_ENDING)


class RacingState(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')

        msg = await self.receive(timeout=10)

        if msg:
            pass


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

    async def setup(self):
        fsm = DriverBehaviour()
        fsm.add_state(name=STATE_DESIRE, state=DesireToRaceState(), initial=True)
        fsm.add_state(name=STATE_GATHER_INFO, state=GatherTrackInfoState())
        fsm.add_state(name=STATE_RACING, state=RacingState())
        fsm.add_state(name=STATE_ENDING, state=Ending())

        fsm.add_transition(source=STATE_DESIRE, dest=STATE_GATHER_INFO)
        fsm.add_transition(source=STATE_DESIRE, dest=STATE_ENDING)
        fsm.add_transition(source=STATE_GATHER_INFO, dest=STATE_RACING)
        self.add_behaviour(fsm)
