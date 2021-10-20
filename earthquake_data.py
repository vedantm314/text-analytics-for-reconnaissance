import os
import time

import requests
import tweepy as tw
import pandas as pd
from datetime import date, timedelta
import configparser
from newsapi import NewsApiClient


class EarthquakeDataCollector:
    config = configparser.ConfigParser()
    config.read("config/config.ini")

    VERBOSE = config.getboolean("default", "verbose")
    DATA_DIR = config["default"]["data_dir"]
    DURATION = config["default"]["duration"]
    MIN_MAGNITUDE = int(config["default"]["min_magnitude"])
    ALERT_LEVELS = config["default"]["alert_levels"].split(",")
    DATE = config["default"]["date"]
    MAX_TWEETS = int(config["default"]["max_tweets"])
    MAX_PAGE = int(config["default"]["max_page"])

    def __init__(self):
        print("initialized")

    def limit_handled(cursor):
        """Handle twitter rate limit."""
        while True:
            try:
                yield cursor.next()
            except tw.RateLimitError:
                time.sleep(1 * 60)

    def get_tweet(self, keys, search_words, date=str(date.today()), max_item=1000, geocode=None):
        consumer_key, consumer_secret, access_token, access_token_secret = keys
        auth = tw.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tw.API(auth, wait_on_rate_limit=True)

        # Define the search term and date
        search_words = search_words + " -filter:retweets"

        # Collect tweets
        tweets = tw.Cursor(api.search, q=search_words, geocode=geocode, since=date, tweet_mode='extended').items(10)

        tweet_data = [[tweet.user.screen_name, tweet.user.location, tweet.created_at,
                       tweet.coordinates, tweet.full_text] for tweet in tweets]
        tweet_df = pd.DataFrame(data=tweet_data, columns=['user', "location", "date", "coordinates", "content"])

        return tweet_df

    def get_news(self, api_key, news_search_words, from_date=str(date.today()), page=2, lang="en"):
        newsapi = NewsApiClient(api_key=api_key)

        # endpoint: /v2/everything
        all_articles = newsapi.get_everything(q=news_search_words,
                                              from_param=from_date,
                                              language=lang,
                                              sort_by='relevancy',
                                              page=page)  # each page is 20 articles

        keywords = {"quake", "earthquake", "tremors"}
        articles = []

        for article in all_articles['articles']:
            if keywords.intersection(article['title'].split()):
                articles.append([article['source']['name'], article['title'], article['url'],
                                 article['publishedAt'][:10], article['content']])

        news = pd.DataFrame(data=articles, columns=['source_name', "title", "url", "date", "content"])

        return news

    def log_earthquakes(self, earthquakes, log_file):
        events = []
        for event in earthquakes:
            properties = event["properties"]
            coordinates = event["geometry"]["coordinates"]
            rupture_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(properties["time"] / 1000))
            country = properties["place"].split(", ")[-1]  # get earthquake country
            events.append([properties["place"], country, properties["mag"], rupture_time,
                           properties["felt"], properties["cdi"], properties["mmi"], properties["alert"],
                           coordinates[0], coordinates[1], coordinates[2], properties["url"], True])

        log = pd.read_csv(log_file)
        new_log = pd.DataFrame(events, columns=log.columns)
        log = pd.concat([log, new_log], ignore_index=True)
        log.drop_duplicates(subset=['place', 'country', 'magnitude', 'rupture_time']
                            , keep='first', inplace=True)
        log.to_csv(log_file, index=False)

    def runDailyUpdate(self):
        keys_parser = configparser.ConfigParser()
        keys_parser.read('config/keys.ini')
        twitter_keys = [keys_parser['tweepyapi_key']['consumer_key'],
                        keys_parser['tweepyapi_key']['consumer_secret'],
                        keys_parser['tweepyapi_key']['access_token'],
                        keys_parser['tweepyapi_key']['access_token_secret']
                        ]
        news_key = keys_parser['newsapi_key']['api_key']

        # Query USGS and get social media and news data
        today = date.today()
        print("Today is: ", today)

        # Yesterday date
        yesterday = today - timedelta(days=67)
        print("Query date: ", yesterday)

        log_file = self.runDailyUSGSQuery(yesterday)

        self.runTweetAndNewsCollection(log_file, yesterday, twitter_keys, news_key)

    def runDailyUSGSQuery(self, query_date):
        # Create earthquake log if not existed
        log_file = os.path.join(os.getcwd(), self.DATA_DIR, "earthquakes_log.csv")
        log_path = os.path.join(os.getcwd(), self.DATA_DIR)

        if (not os.path.exists(log_path)):
            os.mkdir(log_path)

        if not os.path.isfile(log_file):
            log = pd.DataFrame(columns=['place', 'country', 'magnitude', 'rupture_time',
                                        'felt', 'cdi', 'mmi', 'alert',
                                        'longitude', 'latitude', 'depth', 'url', 'collect_data'])
            log.to_csv(log_file, index=False)

        # Query earthquake with magnitude >= 5 and alert level yellow, orange, red
        for alert in self.ALERT_LEVELS:
            earthquakes = self.get_usgs(self.MIN_MAGNITUDE, alert, query_date)

            if len(earthquakes) > 0:
                self.log_earthquakes(earthquakes, log_file)

        return log_file

    def runTweetAndNewsCollection(self, log_file, query_date, twitter_keys, news_key):
        log = pd.read_csv(log_file)
        # Change collect_data flag to False for events longer than DURATION
        duration = pd.to_datetime(query_date.today()) - pd.to_datetime(log.rupture_time)
        log.loc[duration > pd.to_timedelta(self.DURATION), "collect_data"] = False

        # Collect social media and news data for recent earthquakes within DURATION
        events = log[log.collect_data == True]

        earthquake_tweet = {}
        earthquake_news = {}

        for rupture_time, country in zip(events.rupture_time, events.country):
            rupture_date = rupture_time.split()[0]

            # Collect tweets
            twitter_search_words = country + "+earthquake"

            tweet_df = self.get_tweet(twitter_keys, twitter_search_words, query_date, self.MAX_TWEETS)
            earthquake_tweet[(rupture_date, country)] = tweet_df

            # Collect news
            news_search_words = '+("earthquake" AND "{}")'.format(country)
            news_df = self.get_news(news_key, news_search_words, query_date, self.MAX_PAGE)
            earthquake_news[(rupture_date, country)] = news_df

        # Store tweet and news to csv file
        for (rupture_date, country) in earthquake_tweet.keys():
            tweet_file = os.path.join(os.getcwd(), self.DATA_DIR, "twitter",
                                      "{}_{}_earthquake.csv".format(rupture_date, country))
            news_file = os.path.join(os.getcwd(), self.DATA_DIR, "news",
                                     "{}_{}_earthquake.csv".format(rupture_date, country))

            # Create new csv if file not exited; otherwise append to existing file
            if not os.path.isfile(tweet_file):
                #    os.mkdir(os.path.join(os.getcwd(), DATA_DIR, "twitter"))

                earthquake_tweet[(rupture_date, country)].to_csv(tweet_file, index=False)
            else:
                current_df = pd.read_csv(tweet_file)
                new_df = earthquake_tweet[(rupture_date, country)]
                tweet_df = pd.concat([current_df, new_df])
                tweet_df.to_csv(tweet_file, index=False)

            if not os.path.isfile(news_file):
                #   os.mkdir(os.path.join(os.getcwd(), DATA_DIR, "news"))

                earthquake_news[(rupture_date, country)].to_csv(news_file, index=False)
            else:
                current_df = pd.read_csv(news_file)
                new_df = earthquake_news[(rupture_date, country)]
                news_df = pd.concat([current_df, new_df])
                news_df.to_csv(news_file, index=False)

    def get_usgs(self, min_magnitude, alert, date):
        parameters = {"minmagnitude": min_magnitude,
                      "alertlevel": alert,
                      "starttime": date}

        URL = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&"

        # Format url parameters: https://earthquake.usgs.gov/fdsnws/event/1/#parameters
        url_params = "&".join(["{}={}".format(key, value) for key, value in parameters.items()])
        URL += url_params

        response = requests.get(URL)
        earthquakes = response.json()['features']
   
        if self.VERBOSE: print("{0} {1} earthquake today.".format(len(earthquakes), alert))

        return earthquakes
