import json
import requests


from pleroma_bot.i18n import _
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
    for t_user in self.twitter_username:
        url = f"{self.twitter_base_url_v2}/users/by/username/{t_user}"
        params = {}
        params.update(
            {
                "user.fields": "created_at,description,entities,id,location,"
                               "name,pinned_tweet_id,profile_image_url,"
                               "protected,url,username,verified,withheld",
                "expansions": "pinned_tweet_id",
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
            url, headers=self.header_twitter, auth=self.auth, params=params
        )
        if not response.ok:
            response.raise_for_status()
        user = json.loads(response.text)["data"]
        self.bio_text[t_user] = (
            f"{self.bio_text['_generic_bio_text']}{user['description']}"
            if self.twitter_bio
            else f"{self.bio_text['_generic_bio_text']}"
        )
        # Check if user has profile image
        if "profile_image_url" in user.keys():
            # Get the highest quality possible
            profile_img_url = user["profile_image_url"].replace("_normal", "")
            self.profile_image_url[t_user] = profile_img_url
        self.display_name[t_user] = user["name"]
        self.twitter_ids[user["id"]] = user["username"]
        # TODO: Migrate to v2 when profile_banner is available users endpoint
        twitter_user_url = (
            f"{self.twitter_base_url}"
            f"/users/show.json?screen_name="
            f"{t_user}"
        )
        response = requests.get(
            twitter_user_url, headers=self.header_twitter, auth=self.auth
        )
        if not response.ok:
            response.raise_for_status()
        user = json.loads(response.text)
        # Check if user has banner image
        if "profile_banner_url" in user.keys():
            base_banner_url = user["profile_banner_url"]
            self.profile_banner_url[t_user] = f"{base_banner_url}/1500x500"
    return


def _get_tweets(
        self,
        version: str,
        tweet_id=None,
        start_time=None,
        t_user=None):
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
            for t_user in self.twitter_username:
                twitter_status_url = (
                    f"{self.twitter_base_url}"
                    f"/statuses/user_timeline.json?screen_name="
                    f"{t_user}"
                    f"&count={str(self.max_tweets)}&include_rts=true"
                )
                response = requests.get(
                    twitter_status_url,
                    headers=self.header_twitter,
                    auth=self.auth
                )
                if not response.ok:
                    response.raise_for_status()
                tweets = json.loads(response.text)

            return tweets
    elif version == "v2":
        tweets_v2 = self._get_tweets_v2(
            tweet_id=tweet_id, start_time=start_time, t_user=t_user
        )
        return tweets_v2
    else:
        raise ValueError(_("API version not supported: {}").format(version))


def _get_tweets_v2(
    self,
    start_time,
    tweet_id=None,
    next_token=None,
    previous_token=None,
    count=0,
    tweets_v2=None,
    t_user=None
):
    if not (3200 >= self.max_tweets > 10):
        global _
        error_msg = _(
            "max_tweets must be between 10 and 3200. max_tweets: {}"
        ).format(self.max_tweets)
        raise ValueError(error_msg)
    params = {}
    previous_token = next_token
    max_tweets = self.max_tweets
    diff = max_tweets - count
    if diff == 0 or diff < 0:
        return tweets_v2
    # Tweet number must be between 10 and 100 for search
    if count:

        max_results = diff if diff < 100 else 100
    else:
        max_results = max_tweets if 100 > self.max_tweets > 10 else 100
    # round up max_results to the nearest 10
    max_results = (max_results + 9) // 10 * 10
    if tweet_id:
        url = f"{self.twitter_base_url_v2}/tweets/{tweet_id}"
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
            url, headers=self.header_twitter, auth=self.auth, params=params
        )

        if not response.ok:
            response.raise_for_status()
        response = json.loads(response.text)
        return response
    else:
        params.update({"max_results": max_results})

        url = (
            f"{self.twitter_base_url_v2}/users/by?"
            f"usernames={t_user}"
        )
        response = requests.get(
            url, headers=self.header_twitter, auth=self.auth
        )
        if not response.ok:
            response.raise_for_status()
        response = json.loads(response.text)
        twitter_user_id = response["data"][0]["id"]

        url = f"{self.twitter_base_url_v2}/users/{twitter_user_id}/tweets"
        if next_token:
            params.update({"pagination_token": next_token})

        params.update(
            {
                "start_time": start_time,
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
        # TODO: Tidy up this mess
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
        count += response.json()["meta"]["result_count"]
        if next_token and next_token != previous_token:
            self._get_tweets_v2(
                start_time=start_time,
                tweets_v2=tweets_v2,
                next_token=next_token,
                previous_token=previous_token,
                count=count,
                t_user=t_user
            )
    except KeyError:
        pass

    return tweets_v2


@spinner(_("Gathering tweets... "))
def get_tweets(self, start_time):
    t_utweets = {}
    self.result_count = 0
    tweets_merged = {
        "data": [],
        "includes": {},
    }
    try:
        for t_user in self.twitter_username:
            t_utweets[t_user] = self._get_tweets(
                "v2",
                start_time=start_time,
                t_user=t_user
            )
            self.result_count += t_utweets[t_user]["meta"]["result_count"]
            tweets_merged["meta"] = {}

        for user in t_utweets:
            includes = ["users", "tweets", "media", "polls"]
            for include in includes:
                try:
                    _ = t_utweets[user]["includes"][include]
                except KeyError:
                    t_utweets[user]["includes"].update({include: []})
                    _ = t_utweets[user]["includes"][include]
            for include in includes:
                try:
                    _ = tweets_merged["includes"][include]
                except KeyError:
                    tweets_merged["includes"].update({include: []})
                    _ = tweets_merged["includes"][include]

            tweets_merged["data"].extend(t_utweets[user]["data"])
            for in_user in t_utweets[user]["includes"]["users"]:
                tweets_merged["includes"]["users"].append(in_user)  # pragma
            for tweet_include in t_utweets[user]["includes"]["tweets"]:
                tweets_merged["includes"]["tweets"].append(tweet_include)
            for media in t_utweets[user]["includes"]["media"]:
                tweets_merged["includes"]["media"].append(media)
            for poll in t_utweets[user]["includes"]["polls"]:
                tweets_merged["includes"]["polls"].append(poll)
            tweets_merged["meta"][user] = t_utweets[user]["meta"]
    except KeyError:
        pass

    return tweets_merged
