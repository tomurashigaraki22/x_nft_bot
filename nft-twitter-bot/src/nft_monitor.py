import os
import tweepy
from dotenv import load_dotenv
load_dotenv
import datetime
import requests
import logging
import time
from datetime import timedelta
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TRADEPORT_API_URL = "https://fub.direct/1/5fJOsEAC2ficioqOowQsz3YUhewaNijoUNrU4lJU45YQtaANAql9fHxvOUa0nAjEbFAmQE8piV82fhmOCwbyK53z0ews0ybfWA1_mGE41gU/https/api.indexer.xyz/graphql"
# Botter_NFt = '07a1345f-7020-4b47-9fa8-b9d77cddeedd'
Botter_NFt = '3f7accce-3128-460f-aa9c-e8ab91831af7'
POLL_INTERVAL = 1000 
TRADEPORT_API_URL = "https://api.indexer.xyz/graphql"
# TRADEPORT_API_URL = "https://graphql.tradeport.xyz/"


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
            #change hours = 24 to the nnumber you want to check for new NFTs for eg 24 hours = 24
            #change block_time to the time you want to start checking for new NFTs eg 24 hours ago = 24 hours ag
            "block_time": {
                "_gt": (datetime.datetime.now(datetime.UTC) - timedelta(minutes=60)).isoformat()
            }
        }
    }
    
    try:
        response = requests.post(
            TRADEPORT_API_URL,
            json={"query": query, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "x-api-user": "botter",
                "x-api-key": "Xt85IOE.c2aba8546f7af76c0f3520240942c716"
            }
        )
        print(f"Response: {response.text}")
        
        # Check if the response is successful before parsing JSON
        if response.status_code == 200:
            response_json = response.json()
            print(f"Response JSON: {response_json}")
            return response_json["data"]["sui"]["listings"]
        else:
            print(f"API Error: Status code {response.status_code}, Response: {response.text}")
            return []
    except Exception as e:
        print(f"API Error: {str(e)}")
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

def process_listing(listing):
    """Process a new listing and post a tweet"""
    # Check if we've already processed this listing
    if listing["id"] in processed_listings:
        return
        
    # Add to processed listings
    processed_listings.add(listing["id"])
    
    # Create and post tweet
    tweet = create_tweet(listing)
    try:
        # Add delay between tweets to respect rate limits
        time.sleep(10)  # Wait 1 minute between tweets
        client.create_tweet(text=tweet)
        logger.info(f"Posted tweet for listing {listing['id']}")
    except Exception as e:
        logger.error(f"Error posting tweet: {str(e)}")
        if "429" in str(e):  # Rate limit error
            logger.info("Rate limit hit, waiting 15 minutes...")
            time.sleep(900)  # Wait 15 minutes before retrying
            try:
                client.create_tweet(text=tweet)
                logger.info(f"Retry successful for listing {listing['id']}")
            except Exception as retry_e:
                logger.error(f"Retry failed: {retry_e}")

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

if __name__ == "__main__":
    main()