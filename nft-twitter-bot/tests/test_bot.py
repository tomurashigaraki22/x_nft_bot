import unittest
from src.bot import Bot

class TestBot(unittest.TestCase):
    def setUp(self):
        self.bot = Bot()

    def test_bot_initialization(self):
        self.assertIsNotNone(self.bot)

    def test_bot_run(self):
        # Assuming the bot has a run method
        self.bot.run()
        self.assertTrue(self.bot.is_running)

if __name__ == '__main__':
    unittest.main()