import os
import tweepy
from dotenv import load_dotenv
load_dotenv
from datetime import datetime
import requests
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TRADEPORT_API_URL = "https://fub.direct/1/5fJOsEAC2ficioqOowQsz3YUhewaNijoUNrU4lJU45YQtaANAql9fHxvOUa0nAjEbFAmQE8piV82fhmOCwbyK53z0ews0ybfWA1_mGE41gU/https/api.indexer.xyz/graphql"
Botter_NFt = '07a1345f-7020-4b47-9fa8-b9d77cddeedd'
POLL_INTERVAL = 300 


client = tweepy.Client(
    consumer_key="O84X7I7shuIDAL9OPpUPNcbMB",
    consumer_secret="QyarsmwHKBC4lIPyirtbNFNHQRTHh1kJXOOKmsamMrw4ClH5tG",
    access_token="1919092855886487552-GBuGmqGVFvXld2nZVHet5vvbhQ6nkP",
    access_token_secret="T2bwHTMYq2XTtSp8dA0AN0cdi7JbbsHRscK69YBio0SdR"
)





# Track processed listings
processed_listings = set()

def fetch_new_listings():
    """Fetch recently listed NFTs using the optimized query"""
    query = """
    query fetchCollectionListedItems(
      $where: listings_bool_exp!
      $limit: Int!
    ) {
      sui {
        listings(
          where: $where
          order_by: {block_time: desc}
          limit: $limit
        ) {
          id
          price
          price_str
          block_time
          market_name
          nft {
            name
            token_id
            media_url
            lastSale: actions(
              where: {type: {_in: ["buy", "accept-collection-bid", "accept-bid"]}}
              limit: 1
            ) {
              price
            }
          }
        }
      }
    }
    """
    
    variables = {
        "limit": 10,
        "where": {
            "nft": {"collection_id": {"_eq": Botter_NFt}},
            "block_time": {
                "_gt": (datetime.utcnow() - timedelta(minutes=5)).isoformat()
            }
        }
    }
    
    try:
        response = requests.post(
            TRADEPORT_API_URL,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"}
        )
        return response.json()["data"]["sui"]["listings"]
    except Exception as e:
        print(f"API Error: {e}")
        return []

def create_tweet(listing):
   #tweet content creation
    botter = listing["nft"]["name"] or f"Token #{listing['nft']['token_id']}"
    price = float(listing["price_str"]) if listing["price_str"] else listing["price"]/1e9
    last_sale = listing["nft"]["lastSale"][0]["price"]/1e9 if listing["nft"]["lastSale"] else None
    
    tweet = f"""🚀 New NFT Listing Alert!

🆕 New Listing: {botter}

💰 Price: {price:.2f} SUI
{f"📉 Last Sale: {last_sale:.2f} SUI" if last_sale else ""}
🛒 Buy now: https://tradeport.xyz/sui/nft/{listing['nft']['token_id']}

#NFT #Sui #TradePort"""
    
    return tweet

def main():
    logger.info("Starting NFT monitor bot")
    while True:
        try:
            listings = fetch_new_listings()
            if not listings:
                logger.info("No new listings found")
                continue
                
            for listing in listings:
                process_listing(listing)
                
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            
        time.sleep(POLL_INTERVAL)