## Unreleased
## Added

## Fixed

- Fixed posting only the first media element in a multiple media tweet

## Upgrade notes

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
