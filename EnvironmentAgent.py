import asyncio
from time import time
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, FSMBehaviour, State
from spade.message import Message

from utils import parse_float, parse_int
from Driver import Driver

helloMessage = """Race Simulator Agent reporting for duty!"""
startHelpMessage = """To begin a race type:
start <name of race>"""
paramsHelpMessage = """To provide the track parameters type:
<length> <safe velocity>
track segment with length <length> and maximum safe velocity of <safe velocity>
or
to finish passing parameters type:
finish"""

STARTING = "STARTING"
COLLECTING_PARAMS = "COLLECTING_PARAMS"
SUBSCRIBING_TO_DRIVER = "SUBSCRIBING_TO_DRIVER"
BROADCASTING_RACE = "BROADCASTING_RACE"
CHOOSING_PARTICIPANTS = "CHOOSING_PARTICIPANTS"
STARTING_RACE = "STARTING_RACE"
RACING = "RACING"
FINISHING = "FINISHING"
MAX_DRIVERS = 5


class EnvironmentBehavior(FSMBehaviour):
    async def on_start(self):
        print(f'{self.__class__.__name__}: starting.')

    async def on_end(self):
        print(f'{self.__class__.__name__}: ending.')
        self.agent.kill()


class Starting(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')

        msg = await self.receive(timeout=180)  # wait for a message for 180 seconds

        if not msg:
            print(f'{self.__class__.__name__}: received no message, terminating!')
            return

        reply = msg.make_reply()
        parsed_msg = msg.body.lower().split(" ")

        if parsed_msg[0] == "start" and len(parsed_msg) != 1:
            print(f'{self.__class__.__name__}: starting new race!')

            self.agent.race_name = " ".join(parsed_msg[1:])
            reply.body = "Race '{}' defined. Waiting for track parameters".format(self.agent.race_name)
            next_state = COLLECTING_PARAMS
        else:
            reply.body = startHelpMessage
            next_state = STARTING

        await self.send(reply)

        self.set_next_state(next_state)


class CollectingParams(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')

        msg = await self.receive(timeout=30)  # wait for a message for 180 seconds

        if not msg:
            print(f'{self.__class__.__name__}: received no message, terminating!')
            return

        reply = msg.make_reply()
        parsed_msg = msg.body.lower().split(" ")

        if len(parsed_msg) == 2 and parse_float(parsed_msg[0]) and parse_float(parsed_msg[1]):
            print(f'{self.__class__.__name__}: got param!')

            length = float(parsed_msg[0])
            max_vel = float(parsed_msg[1])

            self.agent.track.append((length, max_vel))
            reply.body = "Got Your params: length='{}', max_vel='{}'".format(self.agent.track[-1][0],
                                                                             self.agent.track[-1][1])
            next_state = COLLECTING_PARAMS
        elif len(parsed_msg) == 1 and parsed_msg[0] == 'finish':
            print(f'{self.__class__.__name__}: finishing!')

            reply.body = "Finished passing parameters! Broadcasting race..."
            next_state = SUBSCRIBING_TO_DRIVER
        elif len(parsed_msg) == 2 and parsed_msg[0] == 'laps' and parse_int(parsed_msg[1]):
            print(f'{self.__class__.__name__}: got laps number!')

            self.agent.laps = int(parsed_msg[1])

            reply.body = "Got Your laps number: laps='{}'".format(self.agent.laps)
            next_state = COLLECTING_PARAMS
        else:
            reply.body = paramsHelpMessage
            next_state = COLLECTING_PARAMS

        await self.send(reply)

        self.set_next_state(next_state)


class SubscribingToDrivers(State):
    def on_available(self, jid):
        print("[{}] Agent {} is available.".format(self.agent.name, jid.split("@")[0]))

    def on_subscribed(self, jid):
        print("[{}] Agent {} has accepted the subscription.".format(self.agent.name, jid.split("@")[0]))
        print("[{}] Contacts List: {}".format(self.agent.name, self.agent.presence.get_contacts()))

    def on_subscribe(self, jid):
        print("[{}] Agent {} asked for subscription. Let's aprove it.".format(self.agent.name, jid.split("@")[0]))
        self.presence.approve(jid)

    async def run(self):
        print(f'{self.__class__.__name__}: running')
        self.presence.on_subscribe = self.on_subscribe
        self.presence.on_subscribed = self.on_subscribed
        self.presence.on_available = self.on_available
        self.presence.set_available()
        for jid in self.agent.drivers_jids:
            self.presence.subscribe(jid)

        await asyncio.sleep(10),
        self.set_next_state(BROADCASTING_RACE)


class BroadcastingRace(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')

        for driver in self.agent.presence.get_contacts():
            print(driver)
            msg = Message(to=str(driver))
            msg.body = f'racename {self.agent.race_name}'
            await self.send(msg)

        self.set_next_state(CHOOSING_PARTICIPANTS)


class ChoosingParticipants(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')

        msg = await self.receive(timeout=5)

        if msg:
            parsed_msg = msg.body.lower().split(" ")
            if len(parsed_msg) == 1 and parsed_msg[0] == self.agent.race_name:
                self.agent.participants.append(Driver(msg.sender))

            print(self.agent.participants)

            if len(self.agent.participants) < MAX_DRIVERS:
                self.set_next_state(CHOOSING_PARTICIPANTS)
            else:
                self.set_next_state(STARTING_RACE)
        else:
            self.set_next_state(STARTING_RACE)


class StartingRace(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')

        message_body = f'starting {self.agent.race_name}'
        for segment in self.agent.track:
            message_body += f' {segment[0]}'

        for driver in self.agent.participants:
            print(driver)
            msg = Message(to=str(driver.jid))
            msg.body = message_body
            await self.send(msg)

        self.set_next_state(RACING)


class Racing(State):
    async def run(self):
        # print(f'{self.__class__.__name__}: running')

        msg = await self.receive(timeout=0.01)

        if msg:
            parsed_msg = msg.body.lower().split(" ")
            if parsed_msg[0] == "acceleration":
                for driver in self.agent.participants:
                    if driver.jid == msg.sender:
                        driver.acceleration = float(parsed_msg[1])

        if time() - self.agent.last_update_time > 1:
            for driver in self.agent.participants:
                driver.move(time() - self.agent.last_update_time)
                # TODO add crash evaluation
                message = Message(to=str(driver.jid))
                message.body = f'status {driver.position} {driver.velocity} {driver.acceleration} {driver.laps}'
                await self.send(message)

            self.agent.last_update_time = time()

        self.set_next_state(RACING)


class EnvironmentAgent(Agent):
    def __init__(self, jid, password, drivers_jids):
        super().__init__(jid, password)
        self.track = []
        self.laps = 1
        self.race_name = ""
        self.drivers_jids = drivers_jids
        self.participants = []
        self.last_update_time = time()

    async def setup(self):
        print(f'{self.__class__.__name__}: running')
        env_behav = EnvironmentBehavior()

        env_behav.add_state(name=STARTING, state=Starting(), initial=True)
        env_behav.add_state(name=COLLECTING_PARAMS, state=CollectingParams())
        env_behav.add_state(name=SUBSCRIBING_TO_DRIVER, state=SubscribingToDrivers())
        env_behav.add_state(name=BROADCASTING_RACE, state=BroadcastingRace())
        env_behav.add_state(name=CHOOSING_PARTICIPANTS, state=ChoosingParticipants())
        env_behav.add_state(name=STARTING_RACE, state=StartingRace())
        env_behav.add_state(name=RACING, state=Racing())

        env_behav.add_transition(source=STARTING, dest=STARTING)
        env_behav.add_transition(source=STARTING, dest=COLLECTING_PARAMS)
        env_behav.add_transition(source=COLLECTING_PARAMS, dest=COLLECTING_PARAMS)
        env_behav.add_transition(source=COLLECTING_PARAMS, dest=SUBSCRIBING_TO_DRIVER)
        env_behav.add_transition(source=SUBSCRIBING_TO_DRIVER, dest=BROADCASTING_RACE)
        env_behav.add_transition(source=BROADCASTING_RACE, dest=CHOOSING_PARTICIPANTS)
        env_behav.add_transition(source=CHOOSING_PARTICIPANTS, dest=CHOOSING_PARTICIPANTS)
        env_behav.add_transition(source=CHOOSING_PARTICIPANTS, dest=STARTING_RACE)
        env_behav.add_transition(source=STARTING_RACE, dest=RACING)
        env_behav.add_transition(source=RACING, dest=RACING)

        self.add_behaviour(env_behav)
