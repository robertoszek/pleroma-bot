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

!!! warning "Be careful, no validation is performed with the already posted toots/posts by that Fediverse account and you can end up with duplicates posts/toots!"

Additionally, you can provide the ```twitter_username``` value if you only want to force the date for that particular user in your config.

For example:

```console
$ pleroma-bot --forceDate WoolieWoolz
```

## Only gather tweets

If the ```--noProfile``` argument is passed, *only* tweets will be posted. The profile picture, banner, display name and bio will **not** be updated on the Fediverse account and be skipped for all users in the config. 

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

This is particularly useful when trying to circumvent Twitter's API limitations, when you need to copy more than 3200 tweets or from an earlier date than `2010-11-06T00:00:00Z`.

It can also be used as a way of transferring all of your Twitter's account data to a Fediverse instance and making the migration process easier.