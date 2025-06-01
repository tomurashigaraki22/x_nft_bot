import os
import tweepy
from dotenv import load_dotenv
load_dotenv
import datetime
import requests
import logging
import time
from datetime import timedelta
import tempfile
import urllib.request
from tweepy import API, OAuth1UserHandler
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

auth = OAuth1UserHandler(
    "O84X7I7shuIDAL9OPpUPNcbMB",
    "QyarsmwHKBC4lIPyirtbNFNHQRTHh1kJXOOKmsamMrw4ClH5tG",
    "1919092855886487552-GBuGmqGVFvXld2nZVHet5vvbhQ6nkP",
    "T2bwHTMYq2XTtSp8dA0AN0cdi7JbbsHRscK69YBio0SdR"
)
api = API(auth)

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

def fetch_collection_stats():
    """Fetch collection statistics including weekly sales"""
    query = """
    query getCollectionStats($where: collection_stats_bool_exp!) {
      sui {
        collection_stats(where: $where) {
          total_sales
          sales_1w
          floor_price
        }
        recent_sales: actions(
          where: {
            collection_id: {_eq: $collection_id},
            type: {_in: ["buy", "accept-collection-bid", "accept-bid"]}
          }
          order_by: {block_time: desc}
          limit: 1
        ) {
          price
          block_time
        }
      }
    }
    """
    
    variables = {
        "where": {
            "collection_id": {"_eq": Botter_NFt}
        },
        "collection_id": Botter_NFt
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
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "sui" in data["data"]:
                return data["data"]["sui"]
            logger.error(f"Unexpected response structure: {data}")
            return None
        logger.error(f"API Error: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return None

def get_working_image_url(ipfs_hash):
    """Try different IPFS gateways until we find one that works"""
    gateways = [
        f"https://ipfs.io/ipfs/{ipfs_hash}",
        f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}",
        f"https://nftstorage.link/ipfs/{ipfs_hash}",
        f"https://cloudflare-ipfs.com/ipfs/{ipfs_hash}",
        f"https://ipfs.filebase.io/ipfs/{ipfs_hash}"
    ]
    
    for gateway in gateways:
        try:
            response = requests.head(gateway, timeout=5)
            if response.status_code == 200:
                return gateway
        except:
            continue
    
    # If no gateway works, return the first one as fallback
    return gateways[0]

def download_and_upload_image(image_url):
    """Download image from IPFS and upload to Twitter"""
    try:
        # Create a temporary file to store the image
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            # If using IPFS, convert to HTTP URL
            if image_url.startswith('ipfs://'):
                ipfs_hash = image_url.replace('ipfs://', '')
                image_url = f"https://nftstorage.link/ipfs/{ipfs_hash}"
            
            # Download the image
            urllib.request.urlretrieve(image_url, tmp_file.name)
            
            # Upload to Twitter using v1.1 API
            media = api.media_upload(filename=tmp_file.name)
            return media.media_id
            
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return None

def create_tweet(listing, collection_stats=None):
    """Create tweet with NFT image and collection stats"""
    try:
        botter = listing["nft"]["name"] or f"Token #{listing['nft']['token_id']}"
        
        # Convert price from lamports to SUI (1 SUI = 1,000,000,000 lamports)
        price = float(listing["price_str"]) / 1_000_000_000 if listing["price_str"] else listing["price"] / 1_000_000_000
        
        # Convert last sale price from lamports to SUI
        last_sale = listing["nft"]["lastSale"][0]["price"] / 1_000_000_000 if listing["nft"]["lastSale"] else None
        
        # Get image URL and upload to Twitter
        media_url = listing["nft"]["media_url"]
        media_id = download_and_upload_image(media_url)
        
        stats_text = ""
        if collection_stats and "collection_stats" in collection_stats:
            stats = collection_stats["collection_stats"]
            weekly_sales = stats.get("sales_1w", 0)
            floor_price = float(stats.get("floor_price", 0)) / 1_000_000_000
            stats_text = f"\n📊 Weekly Sales: {weekly_sales}"
            if floor_price > 0:
                stats_text += f"\n💎 Floor: {floor_price:.2f} SUI"

        tweet = f"""🚀 New NFT Listing Alert!

🆕 New Listing: {botter}
💰 Price: {price:.2f} SUI
{f"📉 Last Sale: {last_sale:.2f} SUI" if last_sale else ""}{stats_text}

#NFT #Sui #TradePort"""
        
        return tweet, media_id
    except Exception as e:
        logger.error(f"Error creating tweet: {e}", exc_info=True)
        return None, None

last_tweet_time = None
TWEET_INTERVAL = 240  # 4 minutes in seconds

def process_listing(listing):
    """Process a new listing and post a tweet with rate limiting"""
    global last_tweet_time
    
    current_time = time.time()
    
    if last_tweet_time and (current_time - last_tweet_time) < TWEET_INTERVAL:
        return
        
    if listing["id"] in processed_listings:
        return
        
    processed_listings.add(listing["id"])
    collection_stats = fetch_collection_stats()
    
    # Create tweet with media
    tweet, media_id = create_tweet(listing, collection_stats)
    
    if tweet and media_id:
        try:
            # Post tweet with media using v2 client
            client.create_tweet(text=tweet, media_ids=[str(media_id)])
            last_tweet_time = current_time
            logger.info(f"Posted tweet for listing {listing['id']}")
        except Exception as e:
            logger.error(f"Error posting tweet: {str(e)}")
            if "429" in str(e):  # Rate limit error
                logger.info("Rate limit hit, waiting 15 minutes...")
                time.sleep(900)
                try:
                    client.create_tweet(text=tweet, media_ids=[str(media_id)])
                    last_tweet_time = time.time()
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