import json
import requests


def _get_twitter_info(self):
    """Updates User object attributes with current Twitter info

    This includes:

    * Bio text
    * Profile image url
    * Banner image url
    * Screen name

    :return: None
    """
    twitter_user_url = (
        f"{self.twitter_base_url}"
        f"/users/show.json?screen_name="
        f"{self.twitter_username}"
    )
    response = requests.get(twitter_user_url, headers=self.header_twitter)
    if not response.ok:
        response.raise_for_status()
    user_twitter = json.loads(response.text)
    self.bio_text = f'{self.bio_text}{user_twitter["description"]}'
    # Check if user has profile image
    if "profile_image_url_https" in user_twitter.keys():
        self.profile_image_url = user_twitter["profile_image_url_https"]
    # Check if user has banner image
    if "profile_banner_url" in user_twitter.keys():
        base_banner_url = user_twitter["profile_banner_url"]
        self.profile_banner_url = f"{base_banner_url}/1500x500"
    self.display_name = user_twitter["name"]
    return


def _get_tweets(self, version: str, tweet_id=None):
    """Gathers last 'max_tweets' tweets from the user and returns them
    as an dict
    :param version: Twitter API version to use to retrieve the tweets
    :type version: string
    :param tweet_id: Tweet ID to retrieve
    :type tweet_id: int

    :returns: last 'max_tweets' tweets
    :rtype: dict
    """
    if version == "v1.1":
        if tweet_id:
            twitter_status_url = (
                f"{self.twitter_base_url}/statuses/"
                f"show.json?id={str(tweet_id)}"
            )
            response = requests.get(
                twitter_status_url, headers=self.header_twitter
            )
            if not response.ok:
                response.raise_for_status()
            tweet = json.loads(response.text)
            return tweet
        else:
            twitter_status_url = (
                f"{self.twitter_base_url}"
                f"/statuses/user_timeline.json?screen_name="
                f"{self.twitter_username}"
                f"&count={str(self.max_tweets)}&include_rts=true"
            )
            response = requests.get(
                twitter_status_url, headers=self.header_twitter
            )
            if not response.ok:
                response.raise_for_status()
            tweets = json.loads(response.text)
            return tweets
    elif version == "v2":
        params = {}
        if tweet_id:
            url = f"{self.twitter_base_url_v2}/tweets/{tweet_id}"
        else:
            url = f"{self.twitter_base_url_v2}/tweets/search/recent"
            # this only gets tweets from last week
            params.update(
                {
                    "max_results": self.max_tweets,
                    "query": f"from:{self.twitter_username}",
                }
            )
        # Tweet number must be between 10 and 100
        if not (100 >= self.max_tweets > 10):
            raise ValueError(
                f"max_tweets must be between 10 and 100. max_tweets: "
                f"{self.max_tweets}"
            )

        params.update(
            {
                "poll.fields": "duration_minutes,end_datetime,id,options,"
                               "voting_status",
                "media.fields": "duration_ms,height,media_key,"
                                "preview_image_url,type,url,width,"
                                "public_metrics",
                "expansions": "attachments.poll_ids,"
                              "attachments.media_keys,author_id,"
                              "entities.mentions.username,geo.place_id,"
                              "in_reply_to_user_id,referenced_tweets.id,"
                              "referenced_tweets.id.author_id",
                "tweet.fields": "attachments,author_id,"
                                "context_annotations,conversation_id,"
                                "created_at,entities,"
                                "geo,id,in_reply_to_user_id,lang,"
                                "public_metrics,"
                                "possibly_sensitive,referenced_tweets,"
                                "source,text,"
                                "withheld",
            }
        )
        response = requests.get(
            url, headers=self.header_twitter, params=params
        )
        if not response.ok:
            response.raise_for_status()
        tweets_v2 = json.loads(response.text)
        return tweets_v2
    else:
        raise ValueError(f"API version not supported: {version}")


def get_tweets(self):
    return self.tweets
