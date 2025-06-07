from src.nft_monitor import main

class Bot:
    def __init__(self):
        self.is_running = False

    def run(self):
        self.is_running = True
        main()

if __name__ == "__main__":
    bot = Bot()
    bot.run()