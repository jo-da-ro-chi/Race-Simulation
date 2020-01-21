import time
import random
import re
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from spade.message import Message
from spade.template import Template


class SenderAgent(Agent):
    class InformBehav(OneShotBehaviour):

        async def run(self):
            courseLength = 4
            courseLength = str(courseLength)
            print("InformBehav running")
            msg = Message(to="car1@blabber.im")     # Instantiate the message
            msg.set_metadata("performative", "inform")  # Set the "inform" FIPA performative
            msg.body = courseLength
            # msgBack = await self.receive(timeout=10000)
            # if msgBack:
            #     print("Message received with content: {}".format(msgBack.body))

            await self.send(msg)
            print("Message sent!")

            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print("SenderAgent started")
        b = self.InformBehav()
        self.add_behaviour(b)


class ReceiverAgent(Agent):
    class RecvBehav(OneShotBehaviour):
        async def run(self):
            print("RecvBehav running")

            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            if msg:
                print("Message received with content: {}".format(msg.body))
                length = re.match(r'[0-9]', format(msg.body))
                if length:
                    finalLength = int(length.group())
                    speed = random.randint(20, 30)
                    time = finalLength / speed
                    print(str(time) + " Speed: " + str(speed) + " m/s")
                    # msgBack = Message(to="environ@blabber.im")
                    # msgBack.set_metadata("performative", "inform")  # Set the "inform" FIPA performative
                    # msgBack.body = "My time is:" + str(time)
                else:
                    print('I dont know the length')

            else:
                print("Did not received any message after 10 seconds")

            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        print("ReceiverAgent started")
        b = self.RecvBehav()
        template = Template()
        template.set_metadata("performative", "inform")
        self.add_behaviour(b, template)


if __name__ == "__main__":
    receiveragent = ReceiverAgent("car1@blabber.im", "123456")
    future = receiveragent.start()
    future.result()  # wait for receiver agent to be prepared.
    senderagent = SenderAgent("environ@blabber.im", "123456")
    senderagent.start()

    while receiveragent.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            senderagent.stop()
            receiveragent.stop()
            break
    print("Agents finished")
