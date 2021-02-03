## [0.8.0] - 2021-01-19

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
