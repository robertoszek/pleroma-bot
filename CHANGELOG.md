## [0.6.0] - 2021-01-07

## Added

- New attribute ```include_rts``` allows choosing whether if retweets are to be posted or ignored.
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
