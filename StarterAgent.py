import time
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message

helloMessage = """Race Simulator Agent reporting for duty!"""
helpMessage = """Messages that I accept:
start <name of race>
    to begin a race and then provide the track parameters:
<length> <safe velocity>
    track segment with length <length> and maximum safe velocity of <safe velocity>
finish
    to finish describing the track and start the race"""


class StarterAgent(Agent):
    class UserInterfaceBehaviour(CyclicBehaviour):
        def __init__(self):
            super().__init__()
            self.track = []
            self.finish = True
            self.processingInput = False
            self.raceName = ""

        async def run(self):
            print(f'{self.__class__.__name__}: running')
            msg = await self.receive(timeout=180)  # wait for a message for 180 seconds
            if msg:
                reply = msg.make_reply()
                # Parsing the message
                parsed_msg = msg.body.lower().split(" ")
                if parsed_msg[0] == "start" and self.finish:
                    print("started new race")
                    # zacznij nowy wątek dla tego użytkownika - w praktyce dodaj do słownika nowy
                    self.raceName = " ".join(parsed_msg[1:])
                    self.processingInput = True
                    self.finish = False
                    reply.body = "Define race {}. Waiting for track parameters".format(self.raceName)

                elif parsed_msg[0] == "finish" and self.processingInput:
                    if len(self.track):
                        # TODO poinformuj/zacznij EnvironmentAgent i przekaz parametry, czekaj az sie zakonczy
                        reply.body = "The race {} has started, please wait for result!".format(self.raceName)
                    else:
                        # zwroc wiadomosc bledu - proba startu wyscigu z pustym torem
                        reply.body = "Wrong track's parameters format. Insert <float> <float> numbers"
                        self.processingInput = False

                elif self.processingInput and not self.finish:
                    length, max_velocity = None, None
                    try:
                        # sprawdz czy to 2 liczby (zmiennoprzecinkowe)
                        length = float(parsed_msg[0])
                        maxvelocity = float(parsed_msg[1])
                        self.track.append((length, maxvelocity))
                        reply.body = "Acknowledged. Waiting for next parameters!"
                    except ValueError:
                        # jesli nie - wiadomosc o bledzie
                        reply.body = "Wrong track's parameters format. Insert <float> <float> numbers"
                else:
                    reply.body = helloMessage + helpMessage

                await self.send(reply)

        async def on_end(self):
            print(f'{self.__class__.__name__}: running')
            await self.agent.stop()

        async def on_start(self):
            print(f'{self.__class__.__name__}: running')

    async def setup(self):
        print(f'{self.__class__.__name__}: running')
        self.add_behaviour(self.UserInterfaceBehaviour())

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
