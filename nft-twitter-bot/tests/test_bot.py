import unittest
from unittest.mock import patch
from src.bot import Bot

class TestBot(unittest.TestCase):
    def setUp(self):
        self.bot = Bot()

    def test_bot_initialization(self):
        self.assertIsNotNone(self.bot)

    @patch('src.bot.main')
    def test_bot_run(self, mock_main):
        self.bot.run()
        self.assertTrue(self.bot.is_running)
        mock_main.assert_called_once()

if __name__ == '__main__':
    unittest.main()