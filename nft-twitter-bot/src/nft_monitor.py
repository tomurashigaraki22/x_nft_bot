import os
import tweepy
from dotenv import load_dotenv
import datetime
import requests
import logging
import time
from datetime import timedelta
import tempfile
import urllib.request
from tweepy import API, OAuth1UserHandler
import threading
import queue
import shelve
import signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

Botter_NFt = os.getenv('COLLECTION_ID', '3f7accce-3128-460f-aa9c-e8ab91831af7')
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 1000))
TRADEPORT_API_URL = "https://api.indexer.xyz/graphql"

# Configurable lookback
LISTING_LOOKBACK_MINUTES = int(os.getenv("LOOKBACK_MINUTES", 60))

client = tweepy.Client(
    consumer_key=os.getenv('consumer_key'),
    consumer_secret=os.getenv('consumer_secret'),
    access_token=os.getenv('access_token'),
    access_token_secret=os.getenv('access_token_secret')
)

auth = OAuth1UserHandler(
    os.getenv("consumer_key"),
    os.getenv("consumer_secret"),
    os.getenv("access_token"),
    os.getenv("access_token_secret")
)
api = API(auth)

# --- Persistent deduplication using shelve ---
PROCESSED_DB = "processed.db"
tweet_queue = queue.Queue()
TWEET_INTERVAL = 240  # 4 minutes in seconds

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
                "_gt": (datetime.datetime.now(datetime.UTC) - timedelta(minutes=LISTING_LOOKBACK_MINUTES)).isoformat()
            }
        }
    }
    retry_count = 1
    while True:
        try:
            response = requests.post(
                TRADEPORT_API_URL,
                json={"query": query, "variables": variables},
                headers={
                    "Content-Type": "application/json",
                    "x-api-user": "botter",
                    "x-api-key": os.getenv("TRADEPORT_API_KEY", "Xt85IOE.c2aba8546f7af76c0f3520240942c716")
                }
            )
            logger.info(f"Response: {response.text}")

            if response.status_code == 200:
                response_json = response.json()
                logger.info(f"Response JSON: {response_json}")
                return response_json["data"]["sui"]["listings"]
            else:
                logger.error(f"API Error: Status code {response.status_code}, Response: {response.text}")
                time.sleep(min(POLL_INTERVAL * retry_count, 300))  # Backoff, max 5 min
                retry_count += 1
        except Exception as e:
            logger.error(f"API Error: {str(e)}")
            time.sleep(min(POLL_INTERVAL * retry_count, 300))
            retry_count += 1

def download_and_upload_image(image_url):
    """Download image from IPFS and upload to Twitter"""
    try:
        if image_url.startswith('ipfs://'):
            ipfs_hash = image_url.replace('ipfs://', '')
            image_url = get_working_image_url(ipfs_hash)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            try:
                urllib.request.urlretrieve(image_url, tmp_file.name)
            except Exception as e:
                logger.error(f"Failed to download image from {image_url}: {e}")
                return None
            media = api.media_upload(filename=tmp_file.name)
        os.remove(tmp_file.name)  # Cleanup temp file
        return media.media_id
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return None

def process_listing(listing):
    """Add new listing to the tweet queue if not already processed."""
    with shelve.open(PROCESSED_DB) as db:
        if listing["id"] in db:
            return
        db[listing["id"]] = True
    tweet_queue.put(listing)

def fetch_collection_stats():
    """Fetch collection statistics including weekly sales"""
    query = """
    query getCollectionStats($where: collection_stats_bool_exp!, $collection_id: uuid!) {
      sui {
        collection_stats(where: $where) {
          collection_id
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
                "x-api-key": os.getenv("TRADEPORT_API_KEY", "Xt85IOE.c2aba8546f7af76c0f3520240942c716")
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
        except Exception as e:
            logger.warning(f"Gateway {gateway} failed: {e}")
            continue
    
    # If no gateway works, return the first one as fallback
    return gateways[0]

def create_tweet(listing, collection_stats=None):
    """Create tweet with NFT image URL and collection stats"""
    try:
        botter = listing["nft"]["name"] or f"Token #{listing['nft']['token_id']}"
        # Truncate botter name if too long
        botter = botter[:40] + '...' if len(botter) > 43 else botter

        # Convert price from lamports to SUI (1 SUI = 1,000,000,000 lamports)
        raw_price = listing.get("price_str") or listing.get("price")
        price = float(raw_price) / 1_000_000_000 if raw_price else 0.0

        # Convert last sale price from lamports to SUI
        last_sale = listing["nft"]["lastSale"][0]["price"] / 1_000_000_000 if listing["nft"]["lastSale"] else None

        # Get image URL and upload to Twitter
        media_url = listing["nft"].get("media_url")
        if not media_url:
            logger.warning(f"No media URL for listing {listing['id']}")
            return None, None

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

View NFT: {media_url}

#NFT #Sui #TradePort"""
        # Truncate tweet if needed
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."

        return tweet, media_id
    except Exception as e:
        logger.error(f"Error creating tweet: {e}", exc_info=True)
        return None, None

def tweet_worker():
    while True:
        listing = tweet_queue.get()
        if listing is None:
            break  # Sentinel to stop the thread
        try:
            collection_stats = fetch_collection_stats()
            tweet, media_id = create_tweet(listing, collection_stats)
            if tweet and media_id:
                client.create_tweet(text=tweet, media_ids=[str(media_id)])
                logger.info(f"Posted tweet for listing {listing['id']}")
        except Exception as e:
            logger.error(f"Error posting tweet: {e}")
        time.sleep(TWEET_INTERVAL)
        tweet_queue.task_done()

def shutdown_handler(sig, frame):
    logger.info("Shutting down...")
    tweet_queue.put(None)
    exit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

def main():
    logger.info("Starting NFT monitor bot")
    worker_thread = threading.Thread(target=tweet_worker, daemon=True)
    worker_thread.start()
    try:
        while True:
            try:
                listings = fetch_new_listings()
                if not listings:
                    logger.info("No new listings found")
                for listing in listings:
                    process_listing(listing)
            except Exception as e:
                logger.error(f"Main loop error: {e}")
            time.sleep(POLL_INTERVAL)
    finally:
        tweet_queue.put(None)  # Stop the worker thread
        worker_thread.join()

if __name__ == "__main__":
    main()