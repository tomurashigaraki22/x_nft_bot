import os
import tweepy
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwitterClient:
    def __init__(self):
        self.api = self.authenticate()

    def authenticate(self):
        auth = tweepy.OAuth1UserHandler(
            os.getenv('TWITTER_API_KEY'),
            os.getenv('TWITTER_API_SECRET_KEY'),
            os.getenv('TWITTER_ACCESS_TOKEN'),
            os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        return tweepy.API(auth)

    def send_tweet(self, message):
        try:
            self.api.update_status(message)
            logger.info("Tweet sent successfully!")
            return True
        except Exception as e:
            logger.error(f"Error sending tweet: {e}")
            return False

    def send_tweet_with_media(self, message, media_path):
        try:
            self.api.update_status_with_media(status=message, filename=media_path)
            logger.info("Tweet with media sent successfully!")
            return True
        except Exception as e:
            logger.error(f"Error sending tweet with media: {e}")
            return False