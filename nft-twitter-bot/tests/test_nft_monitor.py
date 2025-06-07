import unittest
from unittest.mock import patch
from src.nft_monitor import fetch_new_listings

class TestNFTMonitor(unittest.TestCase):

    @patch('src.nft_monitor.requests.post')
    def test_fetch_new_listings(self, mock_post):
        # Mock the API response
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "data": {
                "sui": {
                    "listings": [
                        {
                            "id": "test-id",
                            "price": 1000000000,
                            "price_str": "1000000000",
                            "block_time": "2025-06-02T19:46:41.905",
                            "market_name": "tradeport",
                            "nft": {
                                "name": "Test NFT",
                                "token_id": "0xtest",
                                "media_url": "ipfs://test",
                                "lastSale": []
                            }
                        }
                    ]
                }
            }
        }

        result = fetch_new_listings()
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]['id'], "test-id")

if __name__ == '__main__':
    unittest.main()