import json
import requests


from pleroma_bot._utils import spinner


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
    response = requests.get(
        twitter_user_url, headers=self.header_twitter, auth=self.auth
    )
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


def _get_tweets(self, version: str, tweet_id=None, start_time=None):
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
                twitter_status_url, headers=self.header_twitter, auth=self.auth
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
                twitter_status_url, headers=self.header_twitter, auth=self.auth
            )
            if not response.ok:
                response.raise_for_status()
            tweets = json.loads(response.text)
            return tweets
    elif version == "v2":
        tweets_v2 = self._get_tweets_v2(
            tweet_id=tweet_id, start_time=start_time
        )
        return tweets_v2
    else:
        raise ValueError(f"API version not supported: {version}")


def _get_tweets_v2(
    self,
    start_time,
    tweet_id=None,
    next_token=None,
    previous_token=None,
    tweets_v2=None,
):
    # Tweet number must be between 10 and 100
    if not (100 >= self.max_tweets > 10):
        raise ValueError(
            f"max_tweets must be between 10 and 100. max_tweets: "
            f"{self.max_tweets}"
        )
    params = {}
    previous_token = next_token
    if tweet_id:
        url = f"{self.twitter_base_url_v2}/tweets/{tweet_id}"
    else:
        url = (
            f"{self.twitter_base_url_v2}/users/by?"
            f"usernames={self.twitter_username}"
        )
        response = requests.get(
            url, headers=self.header_twitter, auth=self.auth
        )
        if not response.ok:
            response.raise_for_status()
        response = json.loads(response.text)
        twitter_id = response["data"][0]["id"]

        url = f"{self.twitter_base_url_v2}/users/{twitter_id}/tweets"
        if next_token:
            params.update({"pagination_token": next_token})

        params.update(
            {
                "start_time": start_time,
                "max_results": self.max_tweets,
            }
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
        url, headers=self.header_twitter, params=params, auth=self.auth
    )
    if not response.ok:
        response.raise_for_status()

    if tweets_v2:
        next_tweets = response.json()

        includes = ["users", "tweets", "media", "polls"]
        for include in includes:
            try:
                _ = tweets_v2["includes"][include]
            except KeyError:
                tweets_v2["includes"].update({include: []})
            try:
                _ = next_tweets["includes"][include]
            except KeyError:
                next_tweets["includes"].update({include: []})

        for tweet in next_tweets["data"]:
            tweets_v2["data"].append(tweet)
        for user in next_tweets["includes"]["users"]:
            tweets_v2["includes"]["users"].append(user)
        for tweet_include in next_tweets["includes"]["tweets"]:
            tweets_v2["includes"]["tweets"].append(tweet_include)
        for media in next_tweets["includes"]["media"]:
            tweets_v2["includes"]["media"].append(media)
        for poll in next_tweets["includes"]["polls"]:
            tweets_v2["includes"]["polls"].append(poll)
        tweets_v2["meta"] = next_tweets["meta"]
    else:
        tweets_v2 = json.loads(response.text)

    try:
        next_token = response.json()["meta"]["next_token"]
        if next_token and next_token != previous_token:
            self._get_tweets_v2(
                start_time=start_time,
                tweets_v2=tweets_v2,
                next_token=next_token,
                previous_token=previous_token,
            )
    except KeyError:
        pass

    return tweets_v2


@spinner("Gathering tweets... ")
def get_tweets(self, start_time):
    return self._get_tweets("v2", start_time=start_time)
