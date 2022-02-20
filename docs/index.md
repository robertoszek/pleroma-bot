# Stork (pleroma-bot)


![Stork](/pleroma-bot/images/logo.png)

Mirror your favorite Twitter accounts in the Fediverse, so you can follow their updates from the comfort of your favorite instance. Or migrate your own to the Fediverse using a Twitter [archive](https://twitter.com/settings/your_twitter_data).

[![Build Status](https://travis-ci.com/robertoszek/pleroma-bot.svg?branch=master)](https://app.travis-ci.com/github/robertoszek/pleroma-bot)
[![Version](https://img.shields.io/pypi/v/pleroma-bot.svg)](https://pypi.org/project/pleroma-bot/)
[![codecov](https://codecov.io/gh/robertoszek/pleroma-bot/branch/master/graph/badge.svg?token=0c4Gzv4HjC)](https://codecov.io/gh/robertoszek/pleroma-bot)
[![Python 3.6](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![License](https://img.shields.io/github/license/robertoszek/pleroma-bot)](https://github.com/robertoszek/pleroma-bot/blob/master/LICENSE.md)


[:material-file-document-multiple-outline:  Get started](/pleroma-bot/gettingstarted/installation/){: .md-button } [:material-download-outline: Download](https://github.com/robertoszek/pleroma-bot/releases/latest){: .md-button } [:material-arch: AUR (Arch)](https://aur.archlinux.org/packages/python-pleroma-bot){: .md-button }

You can find this project at: 

|          :fontawesome-brands-github-alt: GitHub           |            :fontawesome-brands-gitlab: Gitlab             |                    :material-tea: Gitea                     |
|:---------------------------------------------------------:|:---------------------------------------------------------:|:--------------------------------------------------------------------:|
| [pleroma-bot](https://github.com/robertoszek/pleroma-bot) | [pleroma-bot](https://gitlab.com/robertoszek/pleroma-bot) | [pleroma-bot](https://gitea.robertoszek.xyz/robertoszek/pleroma-bot) |


## Features
* [x] Can parse a Twitter [archive](https://twitter.com/settings/your_twitter_data), moving all your tweets to the Fediverse
* [x] Retrieves **tweets** and posts them on the Fediverse account
    * [x] Can filter out RTs
    * [x] Can filter out replies
* [x] Media retrieval and upload of multiple **attachments**
    * [x] :material-video: Video
    * [x] :material-file-image: Images
    * [x] :material-animation-play: Animated GIFs 
    * [x] :material-ballot-outline: Polls
* [x] Update Fediverse **profile info** based on the Twitter account
    * [x] *Display name*
    * [x] *Profile picture*
    * [x] *Banner image*
    * [x] *Bio text*
* [x] Customize Fediverse account's **metadata fields** (e.g. point to the original Twitter account)

## Funding
If you feel like supporting the creator or buying him a beer, you can donate through Ko-fi, Liberapay or Buy Me A Coffee:

[![Donate using Liberapay](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/robertoszek/donate) [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/robertoszek) [<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 30px !important;" >](https://www.buymeacoffee.com/robertoszek) <!---  [<img src="https://c5.patreon.com/external/logo/become_a_patron_button.png" alt="Become a Patron!" style="height: 30px !important;" >](https://www.patreon.com/bePatron?u=19859432) --->


| Type                              | Address                                                                                               |
|:----------------------------------|-------------------------------------------------------------------------------------------------------|
| :fontawesome-brands-monero: XMR   | ```899StGytrpBSq6B9i7ca3iKb6pMM77VkcMxoTquAMJSPSq4HTJtavp5Qe4EFtmAuo74vYWDZ1qWnA2s6D8NZ19NZ8eaASBy``` |
| :fontawesome-brands-bitcoin: BTC  | ```bc1qvwnv67gtslll65ya5pa93nqfnrvp4j8r9kdz5k```                                                      |
| :fontawesome-brands-ethereum: ETH | ```0x16f48dc8b7df603da2888e7708f495091080df7d```                                                      |

## Issues

Did you find a bug or do you have any suggestions? 

Please open an issue at [GitHub's issue tracker](https://github.com/robertoszek/pleroma-bot/issues).

If for any reason you would rather not use GitHub, feel free to send an email to [robertoszek@robertoszek.xyz](mailto:robertoszek@robertoszek.xyz) and I'll try to check it out in a timely manner.