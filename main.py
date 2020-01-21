import time
from StarterAgent import StarterAgent

if __name__ == "__main__":

    starteragent = StarterAgent("environ@blabber.im", "123456")
    starteragent.start()

    while starteragent.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            starteragent.stop()
            break
    print("Agents finished")
