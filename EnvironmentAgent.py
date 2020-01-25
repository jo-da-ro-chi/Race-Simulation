import time
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, FSMBehaviour, State
from spade.message import Message

from utils import parse_float

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
BROADCASTING_RACE = "BROADCASTING_RACE"
RACING = "RACING"
FINISHING = "FINISHING"


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

            self.agent.raceName = " ".join(parsed_msg[1:])
            reply.body = "Race '{}' defined. Waiting for track parameters".format(self.agent.raceName)
            next_state = COLLECTING_PARAMS
        else:
            reply.body = startHelpMessage
            next_state = STARTING

        await self.send(reply)

        self.set_next_state(next_state)


class CollectingParams(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')

        msg = await self.receive(timeout=20)  # wait for a message for 180 seconds

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
            next_state = BROADCASTING_RACE
        else:
            reply.body = paramsHelpMessage
            next_state = COLLECTING_PARAMS

        await self.send(reply)

        self.set_next_state(next_state)


class BroadcastingRace(State):
    async def run(self):
        print(f'{self.__class__.__name__}: running')


class EnvironmentAgent(Agent):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.track = []
        self.raceName = ""

    # class EnvironmentBehavior(CyclicBehaviour):
    #     def __init__(self):
    #         super().__init__()
    #         self.track = []
    #         self.finish = True
    #         self.processingInput = False
    #         self.raceName = ""
    #
    #     async def run(self):
    #         pass
    #
    #     async def on_end(self):
    #         print(f'{self.__class__.__name__}: running')
    #         await self.agent.stop()
    #
    #     async def on_start(self):
    #         print(f'{self.__class__.__name__}: running')

    async def setup(self):
        print(f'{self.__class__.__name__}: running')
        env_behav = EnvironmentBehavior()

        env_behav.add_state(name=STARTING, state=Starting(), initial=True)
        env_behav.add_state(name=COLLECTING_PARAMS, state=CollectingParams())
        env_behav.add_state(name=BROADCASTING_RACE, state=BroadcastingRace())
        # env_behav.add_state(name=STARTING, state=Starting())
        # env_behav.add_state(name=STARTING, state=Starting())

        env_behav.add_transition(source=STARTING, dest=STARTING)
        env_behav.add_transition(source=STARTING, dest=COLLECTING_PARAMS)
        env_behav.add_transition(source=COLLECTING_PARAMS, dest=COLLECTING_PARAMS)
        env_behav.add_transition(source=COLLECTING_PARAMS, dest=BROADCASTING_RACE)

        self.add_behaviour(env_behav)

        # Constructor
        # def __init__(self, msg):
        #     super().__init__()
        #     self.reply_template = msg.make_reply()
        #     self.first_message = msg
        #     self.jobs = []
        #
        # async def on_start(self):
        #     self.reply_template.body = helloMessage
        #     await self.send(self.reply_template)
        #
        # async def run(self):
        #     print(f'{self.__class__.__name__}: running')
        #     request = await self.receive(timeout=360)
        #     print(f'{self.__class__.__name__}: received message {request}')
        #     if request and "finish" not in request.body:
        #         if ";" in request.body:
        #             self.reply_template.body = "Acknowledged. I'm ready for further instructions."
        #             await self.send(self.reply_template)
        #
        #             for job, address in addressBook.items():
        #                 t = Template(metadata={'request_id': uuid.uuid4().hex})  # sender=address,
        #                 print(f'{self.__class__.__name__}: creating Query with id {t.metadata["request_id"]}')
        #                 self.jobs.append(QuerryForInfoBehaviour(request.body, address))
        #                 self.agent.add_behaviour(self.jobs[-1], t)
        #         else:
        #             self.reply_template.body = "The pattern is wrong. Use: <topic>; <optional: keywords>"
        #             await self.send(self.reply_template)
        #     else:
        #         self.kill()
        #
        # async def on_end(self):
        #     self.reply_template.body = finishMessage.format(await self.compile_answer())
        #     await self.send(self.reply_template)
        #
        # async def compile_answer(self):
        #     tries = 3
        #     while tries > 0:
        #         finished = all([beh.is_done() for beh in self.jobs])
        #         print([beh.is_done() for beh in self.jobs])
        #         if finished:
        #             break
        #         self.reply_template.body = f"Collecting necessary information... {tries}"
        #         await self.send(self.reply_template)
        #         time.sleep(5)
        #         tries -= 1
        #     resultsFromBehs = [beh.result for beh in self.jobs if beh.is_done() and not beh.error]
        #     return "\n---\n".join(resultsFromBehs)










        # elif parsed_msg[0] == "finish" and self.processingInput:
        #     if len(self.track):
        #         # TODO poinformuj/zacznij EnvironmentAgent i przekaz parametry, czekaj az sie zakonczy
        #         reply.body = "The race {} has started, please wait for result!".format(self.raceName)
        #     else:
        #         # zwroc wiadomosc bledu - proba startu wyscigu z pustym torem
        #         reply.body = "Wrong track's parameters format. Insert <float> <float> numbers"
        #         self.processingInput = False
        #
        # elif self.processingInput and not self.finish:
        #     length, max_velocity = None, None
        #     try:
        #         # sprawdz czy to 2 liczby (zmiennoprzecinkowe)
        #         length = float(parsed_msg[0])
        #         maxvelocity = float(parsed_msg[1])
        #         self.track.append((length, maxvelocity))
        #         reply.body = "Acknowledged. Waiting for next parameters!"
        #     except ValueError:
        #         # jesli nie - wiadomosc o bledzie
        #         reply.body = "Wrong track's parameters format. Insert <float> <float> numbers"