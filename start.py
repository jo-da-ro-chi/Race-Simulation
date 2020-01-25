import time
from EnvironmentAgent import EnvironmentAgent

if __name__ == "__main__":

    agents = []
    agents.append(EnvironmentAgent("environ@blabber.im", "123456"))
    # agents.append(EnvironmentAgent("starter@blabber.im", "123456"))

    for agent in agents:
        agent.start()

    print("Agents started")
    #
    # while agents[0].is_alive():
    #     try:
    #         time.sleep(1)
    #     except KeyboardInterrupt:
    #         agents[0].stop()
    #         break
    # print("Agents finished")
