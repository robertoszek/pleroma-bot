## [1.0.1] 10-02-2022
## Fixed
- Locale issue on Mac if the LANG environment variables were not set
- RTs media attachments being duplicated if the referenced tweet was nested too deep
- Pinned tweets being posted twice if they were part of the more recent batch of retrieved tweets

## Added
- `pleroma-bot` can be run as a daemon now by using the flag `--daemon`.
- A systemd service is automatically installed with the AUR package (and can be found in the repo as `pleroma-bot.service`)

## [1.0.0] 16-01-2022 
## Fixed
- `max_tweets` not accepting values higher than 100
- Video: Not getting the best bitrate version of video attachments in some cases
- Polls: not being retrieved for accounts with protected tweets
- RTs: not getting original tweet media attachments 
## Added
- `twitter_username` value can be a list now, for having multiple Twitter accounts as sources for one target Fediverse account.
- A Twitter [archive](https://twitter.com/settings/your_twitter_data) can be provided with `--archive`([more info in the docs](https://robertoszek.github.io/pleroma-bot/gettingstarted/usage/#using-an-archive))
- Links to Twitter attachments (video, images) are no longer explicitly included on the post's body text by default. You can choose to keep adding them with `keep_media_links`. This option does *not* affect the upload of attachments.
- Youtube links can be replaced with `invidious` and `invidious_base_url`
## Enhancements
- `bio_text` is no longer a mandatory mapping on the config
- Hugely improved performance (around 4x) when processing tweets
- Implemented safety measures for avoiding collision with multiple instances of the bot running at the same time

## [0.8.9] - 2021-12-05
## Added
- ```original_date``` and ```original_date_format``` for adding the original tweet's creation date to the post body
## Fixed
- URL expansion when regex match doesn't include protocol (http, https)

## [0.8.8] - 2021-05-15
## Added
- ```twitter_bio``` for allowing the user to choose if they want to retrieve and append the Twitter bio to their Fediverse user or not.

## [0.8.7] - 2021-05-01
## Added
- ```delay_post``` mapping, for setting how long to wait (in seconds) between each post request to avoid hitting rate limits of the target Fediverse instance
- ```hashtags``` mapping (list), for filtering out tweets which don't match any of them
- ```tweet_ids``` mapping, for listing specific tweets to retrieve and post on the Fediverse account
## Enhancements
- Provide a more meaningful exception message when an HTTP error code 422 is returned when updating the Fediverse profile
- Referenced more directly in the documentation the need to use an account ID instead of a username when targeting a Mastodon instance

## [0.8.6] - 2021-02-27
## Fixed
- Log file handler not being attached when running as a module

## [0.8.5] - 2021-02-23
## Added
- Argument ```--config```, the user can specify a custom path for the config.yml file to be parsed
- Argument ```--log```, the user can specify a custom path for the error.log to create during execution
- Support for localization
## Enhancements
- Created a package in the Arch User Repository: [python-pleroma-bot](https://aur.archlinux.org/packages/python-pleroma-bot)
- Added es_ES translation
- Created [documentation site](https://robertoszek.github.io/pleroma-bot)

## [0.8.0] - 2021-02-03

## Added
- Support for OAuth 1.0a authentication (needed if retrieving tweets from protected accounts)
- Verbose argument ``-v`` for debugging
- ```twitter_username``` can take a list as a value. They are internally broken apart into multiple ```User``` objects

## Fixed
- HTML character entities incorrect escaping in tweet's body
- First run skip condition if the Fediverse had no posts/tweets published as a result of a manual first run

## Enhancements
- Provide feedback when long operations are running (speeen)
- Color output based on logging level

## [0.7.0] - 2021-01-19

## Added
- New and shiny help page
- Checks for first run (no posts/toots on the Fediverse account, or no user folder present)
- Argument ```--forceDate``` to allow setting a starting date for tweet retrieval (optionally forcing it on a user-by-user basis by providing ```twitter_username``` to identify the user on the config file)

## Fixed
- Handle instances being unreachable when trying to get version info to identify their platform

## Enhancements
- Reworked how arguments are parsed and processed with ```argparse```
- Pagination implemented for tweet retrieval (which allows tweets older than one week to be retrieved)

## [0.6.8] - 2021-01-13

## Added
- New config attribute added (```include_replies```) which allows filtering tweets which are replies. Users now can choose whether to drop reply tweets or not (by default ```include_replies``` is ```true```)

## Fixed
- Exception when Twitter display name is longer than 30 Characters and target instance platform is Mastodon (which supports only up to 30)

## Enhancements
- Refactored and aligned the format of old code
- More readable console output when mirroring multiple users 

## [0.6.2] - 2020-01-07

## Fixed
- ```profile_banner_url``` returns a 404 for some users. Now we specifically request the biggest size (1500x500)

## [0.6.1] - 2020-01-07

## Added

- New attribute ```include_rts``` allows choosing whether if retweets are to be posted or ignored.
- New attribute ```file_max_size``` allows setting a maximum size limit for attachments. If exceeded, the attachment will be dropped and won't be uploaded to the Fediverse instance.
- Settings to use different nitter instances (thanks zoenglinghou!)

## Fixed

- Timestamp format for Mastodon instances adjustments
- Sensitivity boolean ignored by Mastodon instances if capitalized

## Enhancements

- Improved Mastodon compatibility

## [0.5.0] - 2020-11-21
## Added

- Support for using the original tweet sensitivity (nsfw flag) when posting on the Fediverse account

## Fixed

- Exception when no tweets are found within the last week (```/tweets/search/recent```)

## Enhancements

- Added tests and 100% code coverage

## Upgrade notes

- Remove the attribute '```sensitive```' from your user section in your ```config.yml``` if you want to honor the 
original tweet's sensitivity instead of forcing it globally for all the posts by that user.

## [0.4.0] - 2020-10-24
## Added

- Added support for polls 🎉 (thanks zoenglinghou!)
- Migrated to Twitter API v2 (falling back to v1.1 for video attachments)

## Enhancements

- Refactored and packaged the code for easy installation. [Link to project at PyPI.](https://pypi.org/project/pleroma-bot/)

## Fixed

- Fixed posting only the first media element in a multiple media tweet
- Fixed video attachments not being downloaded (and uploaded to the Fediverse post)
- Fixed the exception when Twitter user has no profile and/or banner images (thanks zoenglinghou!)

## Upgrade notes

- Place/move your ```config.yml``` to whichever path you want to run ```pleroma-bot```
- If you were using cron, change:
  - ```python3 /path/to/updateInfoPleroma.py noProfile```
  - to ```cd /path/to/your/venv/ && . bin/activate && pleroma-bot noProfile```

## [0.3.0] - 2020-10-07
## Added

- Dynamic attribute loading for the User object from the config file
- Rich text for linking mentions to their Twitter profile
- Allow visibility and sensitivity to be set in the config file

## Fixed

- Replacing the wrong strings in tweet body while expanding URLs
- nitter.net replacement in twitter.com links misbehaviour
- Default to retrieve tweets from the last 48h if Pleroma user has no posts (thanks zoenglinghou!)

## Upgrade notes
1. Replace the field name ```pleroma_url``` with ```pleroma_base_url``` on your ```config.yml```
2. Replace the field name ```twitter_url``` with ```twitter_base_url``` on your ```config.yml```

## [0.2.0] - 2020-08-23
### Added
- Support for tweet attachments
- Allow different usernames for Pleroma and Twitter accounts
- Expand shortened URLs on tweets body
- Support for pinned tweets
- nitter.net URL replacement
- Metadata fields can be defined in ```config.yml```

### Fixed
- RTs only shown body text, with no indication of being RTs

### Upgrade notes
1. Update ```config.yml``` values and fields as described in the ```README.md```

## [0.1.0] - 2020-08-20
### Initial release 
- ```TEXT-ONLY``` This release is good enough for text-only tweet mirroring. All media associated with the tweets will be dropped.
