# Configuration

To run ```pleroma-bot``` you need to create a configuration file first.

The configuration file is written in [YAML](https://yaml.org/). If you're not familiar with it, [this page](https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html) can run you through the basics.

In the config file there are 2 distinct parts, the mappings at the top and a collection of users (each of them being a sequence of mappings).

```yaml
global_mapping: global_value
users:
- user_mapping: user_value
```

You can think of "users" as a [YAML list](https://gettaurus.org/docs/YAMLTutorial/#Lists-and-Dictionaries), in which each entry of the list is denoted by a hyphen/dash (```-```).

This allows you to add as little as 1 user and as much as you need, there's no upper limit to the number of users you can add.

The mappings outside the user sequences, are considered "**global**" mappings and will be applied to *all* users. So if you define the value for ```pleroma_base_url``` at the top, it will apply to all users in your config:

```yaml hl_lines="1"
pleroma_base_url: https://pleroma.instance
users:
- twitter_username: User1
  pleroma_username: MyPleromaUser1
- twitter_username: User2
  pleroma_username: MyPleromaUser2
```

In this example, ```User1``` and ```User2``` share the configured value of ```pleroma_base_url``` at the top (```https://pleroma.instance```).

You can also **override** the "global" mapping within an user if you so choose:

```yaml hl_lines="7"
pleroma_base_url: https://pleroma.instance
users:
- twitter_username: User1
  pleroma_username: MyPleromaUser1
- twitter_username: User2
  pleroma_username: MyPleromaUser2
  pleroma_base_url: https://another.instance
- twitter_username: User3
  pleroma_username: MyPleromaUser3
```

Here, ```User1``` and ```User3``` share the configured value of ```pleroma_base_url``` at the top **but** ```User2```'s ```pleroma_base_url``` value would be ```https://another.instance```.

## Mappings 

Every mapping that ```pleroma-bot``` understands is listed below with a description, which allows you to further customize how each user should behave.


| Mapping              | Optional | Default                    | Description                                                                                                           |
|:---------------------|:--------:|:---------------------------|:----------------------------------------------------------------------------------------------------------------------|
| pleroma_base_url     |    No    |                            | Your Fediverse instance URL                                                                                           |
| max_tweets           |    No    |                            | How many tweets to get in every execution (Twitter's API hard limit is 3,200)                                         |
| twitter_token        |    No    |                            | Twitter bearer token used for authentication                                                                          |
| consumer_key         |   Yes    |                            | OAuth 1.0a Twitter Consumer Key (only needed for protected accounts)                                                  |
| consumer_secret      |   Yes    |                            | OAuth 1.0a Twitter Consumer Secret (only needed for protected accounts)                                               |
| access_token_key     |   Yes    |                            | OAuth 1.0a Twitter Access Token Key (only needed for protected accounts)                                              |
| access_token_secret  |   Yes    |                            | OAuth 1.0a Twitter Access Token Secret (only needed for protected accounts)                                           |
| nitter               |   Yes    | false                      | If Twitter links should be changed to nitter ones                                                                     |
| nitter_base_url      |   Yes    | https://nitter.net         | Change this to your preferred nitter instance                                                                         |
| signature            |   Yes    | false                      | Add a link to the original status                                                                                     |
| media_upload         |   Yes    | false                      | Download Twitter attachments and add them to the Fediverse posts                                                      |
| rich_text            |   Yes    | false                      | Transform mentions to links pointing to the mentioned Twitter profile                                                 |
| include_rts          |   Yes    | false                      | Include RTs when posting tweets in the Fediverse account                                                              |
| include_replies      |   Yes    | false                      | Include replies when posting tweets in the Fediverse account                                                          |
| hashtags             |   Yes    |                            | List of hashtags to use to filter out tweets which don't include any of them                                          |
| visibility           |   Yes    | unlisted                   | Visibility of the post. Must one of the following: public, unlisted, private, direct                                  |
| sensitive            |   Yes    | original tweet sensitivity | Force all posts to be sensitive (NSFW) or not                                                                         |
| file_max_size        |   Yes    |                            | How big attachments can be before being ignored. Examples: "30MB", "1.5GB", "0.5TB"                                   |
| delay_post           |   Yes    | 0.5                        | How long to wait (in seconds) between submitting posts to the Fedi instance (useful when trying to avoid rate limits) |
| tweet_ids            |   Yes    |                            | List of specific tweet IDs to retrieve and post                                                                       |
| twitter_bio          |   Yes    | true                       | Append Twitter's bio to Pleroma/Mastodon target user                                                                  |
| original_date        |   Yes    | false                      | Include the creation date of the tweet on the Fediverse post body                                                     |
| original_date_format |   Yes    | "%Y-%m-%d %H:%M"           | Date format to use when adding the creation date of the tweet to the Fediverse post                                   |
| keep_media_links     |   Yes    | false                      | Keep redundant media links on the tweet text or not (`https://twitter.com/<display_name>/status/<tweet_id>/photo/1`)  |
| invidious            |   Yes    | false                      | If Youtube links should be replaced with invidious ones                                                               |
| invidious_base_url   |   Yes    | https://yewtu.be           | Change this to your preferred invidious instance                                                                      |

There a few mappings *exclusive* to users:

| User mapping     | Optional | Default | Description                                                                       |
|:-----------------|:--------:|:--------|:----------------------------------------------------------------------------------|
| twitter_username |    No    |         | Username of Twitter account to mirror (can be a list)                             |
| pleroma_username |    No    |         | Username of target Fediverse account to post content and update profile           |
| pleroma_token    |    No    |         | Bearer token of target Fediverse account                                          |
| bio_text         |   Yes    |         | Text to be appended to the Twitter account bio text                               |
| fields           |   Yes    |         | Optional metadata fields (sequence of name-value pairs) for the Fediverse profile |



## Example configs

So, with that preamble out of the way.

A minimal config looks something like this:

#### Minimal config

```yaml title="config-minimal.yml.sample"
twitter_base_url: https://api.twitter.com/1.1
pleroma_base_url: https://pleroma.instance
max_tweets: 40
twitter_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
users:
- twitter_username: User1
  pleroma_username: MyPleromaUser1
  pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

#### Complex config

Here's also a more full-fledged config file sample, with 3 users (```KyleBosman```, ```WoolieWoolz``` and ```arstechnica```), which puts all the concepts we've seen together:

```yaml title="config.yml.sample"
twitter_base_url: https://api.twitter.com/1.1
pleroma_base_url: https://pleroma.robertoszek.xyz
nitter_base_url: https://nitter.net
max_tweets: 40
twitter_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# List of users and their attributes
users:
- twitter_username: KyleBosman
  pleroma_username: KyleBosman
  pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  # (optional) keys and secrets for using OAuth 1.0a (for protected accounts)
  consumer_key: xxxxxxxxxxxxxxxxxxxxxxxxx
  consumer_secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  access_token_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  access_token_secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  signature: true
  media_upload: true
  nitter: true
  rich_text: true
  visibility: "unlisted"
  sensitive: false
  original_date: true
  original_date_format: "%Y/%m/%d %H:%M"
  include_rts: false
  include_replies: false
  hashtags:
    - sponsored
  file_max_size: 500MB
  # additional custom-named mappings
  support_account: robertoszek
  # you can use any mapping from 'user' inside a string with {{ mapping_name }} 
  # and it will be replaced with the mapping value. e.g. {{ support_account }}
  bio_text: "\U0001F916 BEEP BOOP \U0001F916 \nI'm a bot that mirrors\
    \ {{ twitter_username }} Twitter's account. \nAny issues please \
    \contact @{{ support_account }} \n \n "
  # Optional metadata fields and values for the Fediverse profile
  fields:
  - name: "\U0001F426 Birdsite"
    value: "{{ twitter_url }}"
  - name: "Status"
    value: "I am afraid I cannot do that."
  - name: "Source"
    value: "https://gitea.robertoszek.xyz/robertoszek/pleroma-bot"
# Mastodon instance example
- twitter_username: WoolieWoolz
  pleroma_username: 24660
  pleroma_base_url: https://botsin.space
  pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  # Mastodon doesn't support rich text!
  rich_text: false
  signature: true
  nitter: true
  visibility: "unlisted"
  media_upload: true
  max_tweets: 50
  bio_text: "\U0001F916 BEEP BOOP \U0001F916 \nI'm a bot that mirrors\
    \ {{ twitter_username }} Twitter's account. \nAny issues please \
    \contact @{{ support_account }} \n \n "
  fields:
  - name: "\U0001F426 Birdsite"
    value: "{{ twitter_url }}"
  - name: "Status"
    value: "I am completely operational."
  - name: "Source"
    value: "https://gitea.robertoszek.xyz/robertoszek/pleroma-bot"
# Minimal config example
- twitter_username: arstechnica
  pleroma_username: mynewsbot
  pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  bio_text: ""
```

## :fontawesome-brands-mastodon: Mastodon
If you use ```pleroma-bot``` with a Mastodon instance, please do take into account that you'll need to fill the ```pleroma_username``` mapping with your Mastodon account ID, *not* the username or nickname.
```yaml hl_lines="3"
# Mastodon instance example
- twitter_username: WoolieWoolz
  pleroma_username: 24660 # <--
  pleroma_base_url: https://botsin.space
  pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  [...]
```
The ease of finding the ID for your Mastodon account varies between instances, sometimes it's as easy as to navigate to your profile and copy it from the URL.

You can try searching for it this way:
```shell
curl 'https://yourmastodon.instance/api/v2/search?q=<username>&resolve=true&limit=5' 
    -H 'Authorization: Bearer xxxxx' 
```