# Usage

Once you have your config ready, launch ```pleroma-bot``` like so:

=== ":material-language-python: Using PyPi"

    ```console
    $ pleroma-bot
    ```

    !!! info "If using a virtual environment, you'll have to activate before you're able to run it"
    ```console
    $ source myenv/bin/activate
    (myenv) $ pleroma-bot
    ```

=== ":material-arch: Using AUR package"

    ```console
    $ pleroma-bot
    ```

=== ":material-git: Using Git"

    ```console
    $ python3 -m pleroma_bot.cli
    ```

!!! note "An ```error.log``` file will be created at the path from which ```pleroma-bot``` is being called (current working directory). Make sure you have write permissions on it"

## First run

When running the bot for the first time it will ask you for the date you wish to start retrieving tweets from.

It will gather *all* tweets from that date up to the present. 
If you don't input any value and press ++enter++ it will default to the oldest date that Twitter's API allows ('```2010-11-06T00:00:00Z```') for tweet retrieval.

To force this behaviour in the future, you can use the ```--forceDate``` argument.


Additionally, you can provide the ```twitter_username``` value if you only want to force the date for that particular user in your config.

For example:

```console
$ pleroma-bot --forceDate TwitterUsername
```

## Only gather tweets

If the ```--noProfile``` argument is used, *only* tweets will be posted.

The profile picture, banner, display name and bio will **not** be updated on the Fediverse account and will be skipped for all users in the config.

Alternatively, you can also choose to use the `no_profile` [mapping on your config](/pleroma-bot/gettingstarted/configuration/#mappings), setting it to `true` on the users you wish to do so:
```yaml hl_lines="5"
- twitter_username: MyTwitterUser
  pleroma_username: MyPleromaUser
  pleroma_base_url: https://fedi.instance
  pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  no_profile: true  # <--
```
This is useful if for whatever reason (data caps, server bandwidth) you prefer not downloading the profile image, banner, etc. every run.

## Custom path for log and config

Arguments ```--config``` and ```--log``` can be used to specify a specific path for the configuration file and where the log file should be written to.

```console
$ pleroma-bot --config /path/to/config.yml --log /path/to/error.log
```

When these arguments are omitted, ```config.yml``` from the current directory will be used as a configuration file and an ```error.log``` file will be written to the current working directory.

## Using an archive

A Twitter [archive](https://twitter.com/settings/your_twitter_data) can also be provided with `--archive`:

```console
$ pleroma-bot --archive /path/to/archive.zip
```

Or using the `archive` mapping in your config file:

```yaml title="config.yml" hl_lines="6"
pleroma_base_url: https://pleroma.instance
users:
- twitter_username: User1
  pleroma_username: MyPleromaUser1
  pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  archive: /path/to/archive.zip
```

This is particularly useful when trying to circumvent Twitter's API limitations, when you need to copy more than 3200 tweets or from an earlier date than `2010-11-06T00:00:00Z`.

It can also be used as a way of transferring all of your Twitter's account data to a Fediverse instance and making the migration process easier.

## Using an RSS feed

You can use RSS feeds as the source of the tweets to post on your Fediverse account.

We recommend using either:

=== "Nitter RSS"
  
    Choose a [nitter instance](https://github.com/zedeus/nitter/wiki/Instances) and use the following format:
    
        https://nitter.instance/<twitter_user>/with_replies/rss
    
    example: `https://nitter.lacontrevoie.fr/github/with_replies/rss`
    
    An then use it in your config in the `rss` mapping:

    ```yaml hl_lines="6"
    pleroma_base_url: https://pleroma.instance
    users:
    - twitter_username: User1
      pleroma_username: MyPleromaUser1
      pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      rss: https://nitter.instance/<twitter_user>/with_replies/rss
    ```

=== "RSSHub"

    Use the following format:

        https://rsshub.app/twitter/user/<twitter_user>/

    example: `https://rsshub.app/twitter/user/github/count=100`

    An then use it in your config in the `rss` mapping:
    
    ```yaml hl_lines="6"
    pleroma_base_url: https://pleroma.instance
    users:
    - twitter_username: User1
      pleroma_username: MyPleromaUser1
      pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
      rss: https://rsshub.app/twitter/user/<twitter_user>/
    ```

## Advanced usage

### Content warnings
By using the `content_warnings` mapping in your config, you can add [content warning](https://docs.joinmastodon.org/user/posting/#cw) topics to a mirrored tweet if keywords from that topic are found within the tweet's text.

```yaml title="config.yml" hl_lines="2-15"
pleroma_base_url: https://pleroma.instance
content_warnings:
  "tetris spoilers":
    - "tspin"
    - "tetrimino"
    - "line clear"
  "dungeon-crawling":
    - "rogue"
    - "rogue-like"
    - "rogue-lite"
  "nippon cartoons":
    - "manga"
    - "anime"
  "spoilers":
    - "#spoilers"
users:
- twitter_username: User1
  pleroma_username: MyPleromaUser1
  pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

For example, if the original tweet was:

!!! quote "Original Tweet :material-twitter:" 
    The ==tspin== was better in the ==manga==
    \#tetris ==#spoilers==
    

Then the resulting content warning using the previous config will be:

        Tetris spoilers, nippon cartoons, spoilers

![Content Warning](/pleroma-bot/images/cw.png)

### Custom replacements
Using the `custom_replacements` mapping on your config you can set text to be replaced on the mirrored tweet before publishing it.

For example, this is particularly useful if you happen to have multiple mirrored accounts but their handles are not an exact match on the Fediverse instance.

`@Linus__Torvalds` may be have the `@TorvaldsBot` handle on your instance, so you would want to replace it with the correct one when they are mentioned by another user you're also mirroring.

And not only that, you can replace any text you wish with whatever you may find useful or relevant for your usecase.

You as key-value pairs on your config. The key at the left will be replaced by whatever value is associated to it:

```yaml title="config.yml" hl_lines="2-6"
pleroma_base_url: https://pleroma.instance
custom_replacements:
    "@replacethishandle": "@withthishandle"
    "@Linus__Torvalds": "@TorvaldsBot"
    "Twitter": "Birdsite"
    "Soccer": "football"
users:
- twitter_username: User1
  pleroma_username: MyPleromaUser1
  pleroma_token: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

So, by using the previous config example if the original tweet was:

!!! quote "Original Tweet :material-twitter:"

    Hey ==*@Linus__Torvalds*== hit me up on ==*Twitter*== DMs for further details on 
    the ==*soccer*== league we're organising on next week's meetup.


The post published on the mirror account would be the following:    

!!! quote "Fediverse Post :fontawesome-solid-robot:"

    Hey ==*@TorvaldsBot*== hit me up on ==*Birdsite*== DMs for further details on 
    the ==*football*== league we're organising on next week's meetup.