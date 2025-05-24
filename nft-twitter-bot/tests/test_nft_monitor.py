import unittest
from src.nft_monitor import check_new_listings

class TestNFTMonitor(unittest.TestCase):
    
    def test_check_new_listings(self):
        # Assuming check_new_listings returns a list of new NFTs
        result = check_new_listings()
        self.assertIsInstance(result, list)
        # Add more assertions based on expected behavior

if __name__ == '__main__':
    unittest.main()