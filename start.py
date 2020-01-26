import time
from EnvironmentAgent import EnvironmentAgent
from DriverAgent import DriverAgent

if __name__ == "__main__":

    drivers_jids = []
    driver_agents = []

    for i in range(1, 2):
        drivers_jids.append(f'car{i}_sag2020@blabber.im')

    for jid in drivers_jids:
        print(jid)
        driver_agents.append(DriverAgent(jid, "123456", {"skill": 0.8, "desire": 1.0, "courageous": 0.64}))

    env_agent = EnvironmentAgent("environ@blabber.im", "123456", drivers_jids)

    port = 50000
    for agent in driver_agents:
        agent.start()
        port = port + 1
        agent.web.start(hostname="127.0.0.1", port=str(port))

    env_agent.start()
    env_agent.web.start(hostname="127.0.0.1", port="60000")

    print("Agents started")

    while env_agent.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            env_agent.stop()
            break
    print("Agents finished")
