import time
import requests

from tqdm import tqdm
from datetime import datetime, timezone

from . import logger
from pleroma_bot.i18n import _

# from pleroma_bot._utils import spinner


def twitter_api_request(method, url,
                        params=None, data=None, headers=None, cookies=None,
                        files=None, auth=None, timeout=None, proxies=None,
                        hooks=None, allow_redirects=True, stream=None,
                        verify=None, cert=None, json=None):
    response = requests.request(
        method=method.upper(),
        url=url,
        headers=headers,
        files=files,
        data=data or {},
        json=json,
        params=params or {},
        auth=auth,
        cookies=cookies,
        hooks=hooks,
    )
    if response.status_code == 429:
        remaining = int(response.headers.get('x-rate-limit-remaining'))
        if remaining == 0:
            limit = int(response.headers.get('x-rate-limit-limit'))
            reset_header = int(response.headers.get('x-rate-limit-reset'))
            reset_time = datetime.utcfromtimestamp(reset_header)
            logger.info(_(
                "Rate limit exceeded. 0 out of {} requests remaining until {}"
                " UTC"
            ).format(limit, reset_time))

            delay = (reset_time - datetime.utcnow()).total_seconds() + 2
            logger.info(_("Sleeping for {}s...").format(round(delay)))
            time.sleep(delay)

            response = twitter_api_request(method, url,
                                           params=params, data=data,
                                           headers=headers, cookies=cookies,
                                           files=files, auth=auth, hooks=hooks,
                                           timeout=timeout, proxies=proxies,
                                           allow_redirects=allow_redirects,
                                           stream=stream, verify=verify,
                                           cert=cert, json=json)
    return response


def _get_twitter_info_guest(self):  # pragma: todo
    from pleroma_bot._processing import _expand_urls

    for t_user in self.twitter_username:
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
        user_twitter = response.json()

        bio_text = user_twitter["description"]
        # Expand bio urls if possible
        if self.twitter_bio:
            bio_short = user_twitter["description"]
            bio = {'text': user_twitter["description"], 'entities': None}
            bio_long = _expand_urls(self, bio)
            max_len = self.max_post_length
            len_bio = len(f"{self.bio_text['_generic_bio_text']}{bio_long}")
            bio_text = bio_long if len_bio < max_len else bio_short
        self.bio_text[t_user] = (
            f"{self.bio_text['_generic_bio_text']}{bio_text}"
            if self.twitter_bio
            else f"{self.bio_text['_generic_bio_text']}"
        )

        # Check if user has profile image
        if "profile_image_url_https" in user_twitter.keys():
            profile_img = user_twitter["profile_image_url_https"]
            self.profile_image_url[t_user] = profile_img
        # Check if user has banner image
        if "profile_banner_url" in user_twitter.keys():
            base_banner_url = user_twitter["profile_banner_url"]
            self.profile_banner_url[t_user] = f"{base_banner_url}/1500x500"
        self.display_name[t_user] = user_twitter["name"]
        if "entities" in user_twitter:
            if "url" in user_twitter["entities"]:
                wb = user_twitter["entities"]["url"]["urls"][0]["expanded_url"]
                self.website = wb


def _get_twitter_info(self):
    """Updates User object attributes with current Twitter info

    This includes:

    * Bio text
    * Profile image url
    * Banner image url
    * Screen name

    :return: None
    """
    from pleroma_bot._processing import _expand_urls

    if self.archive:
        return
    if self.guest:  # pragma: todo
        self._get_twitter_info_guest()
        return
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
        response = twitter_api_request(
            'GET',
            url,
            headers=self.header_twitter,
            auth=self.auth,
            params=params
        )
        if not response.ok:
            response.raise_for_status()
        user = response.json()["data"]
        bio_text = user["description"]
        # Expand bio urls if possible
        if self.twitter_bio:
            user_entities = user["entities"] if "entities" in user else None
            bio_short = user["description"]
            bio = {'text': user['description'], 'entities': user_entities}
            bio_long = _expand_urls(self, bio)
            max_len = self.max_post_length
            len_bio = len(f"{self.bio_text['_generic_bio_text']}{bio_long}")
            bio_text = bio_long if len_bio < max_len else bio_short
        self.bio_text[t_user] = (
            f"{self.bio_text['_generic_bio_text']}{bio_text}"
            if self.twitter_bio
            else f"{self.bio_text['_generic_bio_text']}"
        )
        # Get website
        if "entities" in user and "url" in user["entities"]:
            self.website = user['entities']['url']['urls'][0]['expanded_url']
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
        response = twitter_api_request(
            'GET',
            twitter_user_url,
            headers=self.header_twitter,
            auth=self.auth
        )
        if not response.ok:
            response.raise_for_status()
        user = response.json()
        # Check if user has banner image
        if "profile_banner_url" in user.keys():
            base_banner_url = user["profile_banner_url"]
            self.profile_banner_url[t_user] = f"{base_banner_url}/1500x500"
    return


def _package_tweets_v2(tweets_v1):  # pragma: todo
    tweets = {"data": [], "includes": {}}
    if isinstance(tweets_v1, dict):
        for entity in tweets_v1["entities"]:
            tweets["includes"][entity] = tweets_v1["entities"][entity]
        if "user" in tweets_v1.keys():
            tweets_v1["user"]["id"] = tweets_v1["user"]["id_str"]
            tweets_v1["user"]["username"] = tweets_v1["user"]["screen_name"]
            tweets["includes"]["users"] = [tweets_v1["user"]]
        tweets_v1["text"] = tweets_v1["full_text"]
        tweets_v1["id"] = str(tweets_v1["id"])
        tweets_v1["author_id"] = tweets_v1["user"]["id_str"]
        if "possibly_sensitive" not in tweets_v1.keys():
            tweets_v1["possibly_sensitive"] = False
        retweet_id = None
        quote_id = None
        reply_id = None
        if "retweeted_status_id_str" in tweets_v1.keys():
            retweet_id = tweets_v1["retweeted_status_id_str"]
        if "quoted_status_id_str" in tweets_v1.keys():
            quote_id = tweets_v1["quoted_status_id_str"]
        if "in_reply_to_status_id_str" in tweets_v1.keys():
            reply_id = tweets_v1["in_reply_to_status_id_str"]
        if quote_id or reply_id:
            tweets_v1["referenced_tweets"] = []
            if retweet_id:
                rt = {"id": retweet_id, "type": "retweeted"}
                tweets_v1["referenced_tweets"].append(rt)
            if reply_id:
                reply = {"id": reply_id, "type": "replied_to"}
                tweets_v1["referenced_tweets"].append(reply)
            if quote_id:
                quoted_tw = tweets_v1["quoted_status"]
                quoted_tw["author_id"] = quoted_tw["user"]["id_str"]
                quoted_tw["id"]: quote_id
                quoted_tw["type"] = "quoted"
                tweets_v1["referenced_tweets"].append(quoted_tw)
        tweets["data"] = tweets_v1
    else:
        tweets["meta"] = {"result_count": len(tweets_v1)}
        for tweet_v1 in tweets_v1:
            tweet_v1["text"] = tweet_v1["full_text"]
            tweet_v1["id"] = str(tweet_v1["id"])
            date_twitter = datetime.strftime(
                datetime.strptime(
                    tweet_v1["created_at"], '%a %b %d %H:%M:%S +0000 %Y'
                ),
                '%Y-%m-%dT%H:%M:%S.000Z'
            )
            tweet_v1["created_at"] = date_twitter
            if "possibly_sensitive" not in tweet_v1.keys():
                tweet_v1["possibly_sensitive"] = False
            if "user_id_str" in tweet_v1.keys():
                tweet_v1["author_id"] = tweet_v1["user_id_str"]
            retweet_id = None
            quote_id = None
            reply_id = None
            if "user" in tweet_v1.keys():
                tweet_v1["user"]["id"] = tweet_v1["user"]["id_str"]
                tweet_v1["user"]["username"] = tweet_v1["user"]["screen_name"]
                tweets["includes"]["users"] = [tweet_v1["user"]]
            if "retweeted_status_id_str" in tweet_v1.keys():
                retweet_id = tweet_v1["retweeted_status_id_str"]
            if "quoted_status_id_str" in tweet_v1.keys():
                quote_id = tweet_v1["quoted_status_id_str"]
            if "in_reply_to_status_id_str" in tweet_v1.keys():
                reply_id = tweet_v1["in_reply_to_status_id_str"]
            if quote_id or reply_id or retweet_id:
                tweet_v1["referenced_tweets"] = []
                if retweet_id:
                    rt = {"id": retweet_id, "type": "retweeted"}
                    tweet_v1["referenced_tweets"].append(rt)
                if reply_id:
                    reply = {"id": reply_id, "type": "replied_to"}
                    tweet_v1["referenced_tweets"].append(reply)
                if quote_id:
                    quoted_tw = {"id": quote_id, "type": "quoted"}
                    tweet_v1["referenced_tweets"].append(quoted_tw)
            tweets["data"].append(tweet_v1)
            if "entities" in tweet_v1:
                for entity in tweet_v1["entities"]:
                    tweets["includes"][entity] = tweet_v1["entities"][entity]
        tweets["data"] = sorted(
            tweets["data"], key=lambda i: i["created_at"], reverse=True
        )
    return tweets


def _get_tweets(
        self,
        version: str,
        tweet_id=None,
        start_time=None,
        t_user=None,
        pbar=None):
    """Gathers last 'max_tweets' tweets from the user and returns them
    as a dict
    :param version: Twitter API version to use to retrieve the tweets
    :type version: string
    :param tweet_id: Tweet ID to retrieve
    :type tweet_id: int

    :returns: last 'max_tweets' tweets
    :rtype: dict
    """
    if version == "v1.1" or self.guest:
        if tweet_id:
            twitter_status_url = (
                f"{self.twitter_base_url}/statuses/"
                f"show.json?id={str(tweet_id)}&include_entities=true"
                f"&tweet_mode=extended"
            )
            response = twitter_api_request(
                'GET',
                twitter_status_url,
                headers=self.header_twitter,
                auth=self.auth
            )
            if not response.ok:
                response.raise_for_status()
            tweet = response.json()
            if self.guest:  # pragma: todo
                tweet_v2 = _package_tweets_v2(tweet)
                tweet = tweet_v2
            return tweet
        else:
            for t_user in self.twitter_username:
                if not self.guest:
                    twitter_status_url = (
                        f"{self.twitter_base_url}"
                        f"/statuses/user_timeline.json?screen_name="
                        f"{t_user}"
                        f"&count={str(self.max_tweets)}&include_rts=true"
                    )
                    response = twitter_api_request(
                        'GET',
                        twitter_status_url,
                        headers=self.header_twitter,
                        auth=self.auth
                    )
                    if not response.ok:
                        response.raise_for_status()
                    tweets = response.json()
                else:  # pragma: todo
                    now_ts = int(datetime.now(tz=timezone.utc).timestamp())
                    fmt_date = ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ")
                    for fmt in fmt_date:
                        try:
                            start_time_ts = int(datetime.strptime(
                                start_time, fmt
                            ).replace(tzinfo=timezone.utc).timestamp())
                        except ValueError:
                            pass
                    rts = ""
                    if self.include_rts:
                        rts = "include:nativeretweets"
                    query = (
                        f"(from:{t_user}) "
                        f"since_time:{start_time_ts} until_time:{now_ts} {rts}"
                    )
                    param = {
                        "include_profile_interstitial_type": "1",
                        "include_rts": {str(self.include_rts).lower()},
                        "include_replies": {str(self.include_replies).lower()},
                        "include_quotes": {str(self.include_quotes).lower()},
                        "include_blocking": "1",
                        "include_blocked_by": "1",
                        "include_followed_by": "1",
                        "include_want_retweets": "1",
                        "include_mute_edge": "1",
                        "include_can_dm": "1",
                        "include_can_media_tag": "1",
                        "skip_status": "1",
                        "cards_platform": "Web-12",
                        "include_cards": "1",
                        "include_ext_alt_text": "true",
                        "include_quote_count": "true",
                        "include_reply_count": "1",
                        "tweet_mode": "extended",
                        "include_entities": "true",
                        "include_user_entities": "true",
                        "include_ext_media_color": "true",
                        "include_ext_media_availability": "true",
                        "send_error_codes": "true",
                        "simple_quoted_tweet": "true",
                        "q": query,
                        "count": str(self.max_tweets),
                        "query_source": "typed_query",
                        "pc": "1",
                        "spelling_corrections": "1",
                        "ext": "mediaStats,highlightedLabel",
                    }

                    search_url = (
                        "https://twitter.com/i/api/2/search/adaptive.json"
                    )
                    response = twitter_api_request(
                        'GET',
                        search_url,
                        headers=self.header_twitter,
                        params=param,
                    )
                    if self.proxy and response.status_code == 429:
                        logger.warning(
                            _(
                                "Rate limit exceeded when collecting tweets "
                                "with a guest token. Retrying with a proxy."
                            )
                        )
                        response = self._request_proxy(
                            'GET',
                            search_url,
                            headers=self.header_twitter,
                            params=param
                        )

                    tweets_guest = response.json()["globalObjects"]["tweets"]
                    self.result_count += len(tweets_guest)
                    pbar.update(len(tweets_guest))
                    tweets = []
                    for tweet in tweets_guest:
                        tweets.append(tweets_guest[tweet])
                    tweets_v2 = _package_tweets_v2(tweets)
                    tweets = tweets_v2

            return tweets
    elif version == "v2":
        tweets_v2 = self._get_tweets_v2(
            tweet_id=tweet_id, start_time=start_time, t_user=t_user, pbar=pbar
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
        t_user=None,
        pbar=None
):
    if not (3200 >= self.max_tweets >= 10):
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
                                "public_metrics,alt_text",
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
        response = twitter_api_request(
            'GET',
            url,
            headers=self.header_twitter,
            auth=self.auth,
            params=params
        )

        if not response.ok:
            response.raise_for_status()
        response = response.json()
        return response
    else:
        params.update({"max_results": max_results})

        url = (
            f"{self.twitter_base_url_v2}/users/by?"
            f"usernames={t_user}"
        )
        response = twitter_api_request(
            'GET', url, headers=self.header_twitter, auth=self.auth
        )
        if not response.ok:
            response.raise_for_status()
        response = response.json()
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
                            "public_metrics,alt_text",
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

    response = twitter_api_request(
        'GET', url, headers=self.header_twitter, params=params, auth=self.auth
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
        tweets_v2 = response.json()
    if pbar:
        pbar.update(response.json()["meta"]["result_count"])
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
                t_user=t_user,
                pbar=pbar
            )
    except KeyError:
        pass

    return tweets_v2


# @spinner(_("Gathering tweets... "))
def get_tweets(self, start_time):
    from .i18n import _
    t_utweets = {}
    self.result_count = 0
    tweets_merged = {
        "data": [],
        "includes": {},
    }
    try:
        for t_user in self.twitter_username:
            desc = _("Gathering tweets... ")
            fmt = '{desc}{n_fmt}'
            pbar = tqdm(desc=desc, position=0, total=10000, bar_format=fmt)
            t_utweets[t_user] = self._get_tweets(
                "v2",
                start_time=start_time,
                t_user=t_user,
                pbar=pbar
            )
            pbar.close()
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
