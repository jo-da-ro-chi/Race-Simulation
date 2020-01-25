import time
from spade.agent import Agent
from random import random
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, FSMBehaviour, State
from spade.message import Message
from spade.template import Template

STATE_DESIRE = "STATE_DESIRE"
STATE_REGISTER = "STATE_REGISTER"
STATE_WAIT_START = "STATE_WAIT_START"


class DriverBehaviour(FSMBehaviour):
    async def on_start(self):
        print(f'{self.__class__.__name__}: running')

    async def on_end(self):
        print(f'{self.__class__.__name__}: running')
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


class DesireToRaceState(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')
        msg = await self.receive(timeout=180)  # wait for a message for 180 seconds from EnvironmentAgent
        if msg:
            print("I received message!")
            reply = msg.make_reply()
            parsed_msg = msg.body.lower().split(" ")
            if parsed_msg[0] == "racename":
                print("Desire to participate in race!")
                self.agent.race_name = " ".join(parsed_msg[1:])
                self.agent.desire = (random < (self.agent.params_map["desire"] or 0))
                reply.body = "{}".format(self.agent.race_name)
                print("Sent desire to participate in {}!".format(self.agent.race_name))
                await self.send(reply)
                self.set_next_state(STATE_REGISTER)


class RegisterToRaceState(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')
        msg = await self.receive(timeout=180)  # wait for a message for 180 seconds from EnvironmentAgent
        if msg:
            print("I received message!")
            reply = msg.make_reply()
            parsed_msg = msg.body.lower().split(" ")
            if parsed_msg[0] == self.agent.race_name:
                print("Got answer for desire!")
                if parsed_msg[1] == "yes" and self.agent.desire:
                    print("Registered!")
                    self.agent.registered = True
                    reply.body = "{}".format(self.agent.race_name)
                    self.set_next_state(STATE_WAIT_START)


class WaitForStart(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')
        msg = await self.receive(timeout=180)  # wait for a message for 180 seconds from EnvironmentAgent
        if msg:
            pass


class DriverAgent(Agent):
    def __init__(self, jid, password, params_map):
        super().__init__(jid, password)
        self.race_name = ""
        self.desire = False
        self.registered = False
        self.params_map = params_map

    async def setup(self):
        fsm = DriverBehaviour()
        fsm.add_state(name=STATE_DESIRE, state=DesireToRaceState(), initial=True)
        fsm.add_state(name=STATE_REGISTER, state=RegisterToRaceState())
        fsm.add_state(name=STATE_WAIT_START, state=WaitForStart())
        fsm.add_transition(source=STATE_DESIRE, dest=STATE_REGISTER)
        fsm.add_transition(source=STATE_REGISTER, dest=STATE_WAIT_START)
        self.add_behaviour(fsm)



