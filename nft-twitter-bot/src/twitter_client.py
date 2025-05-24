import os
import tweepy

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
            print("Tweet sent successfully!")
        except Exception as e:
            print(f"Error sending tweet: {e}")