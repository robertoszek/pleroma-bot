# Before running

There are multiple options for using the bot.

You can either choose to use: 

- :fontawesome-solid-file-archive: A [Twitter archive](/pleroma-bot/gettingstarted/usage/#using-an-archive)
- :fontawesome-solid-rss-square: An [RSS feed](/pleroma-bot/gettingstarted/usage/#using-an-rss-feed)
- :fontawesome-solid-address-book: [Guest tokens](/pleroma-bot/gettingstarted/beforerunning/#guest-tokens) without a Developer account 
- :material-account-key: [Twitter tokens](/pleroma-bot/gettingstarted/beforerunning/#twitter-tokens) with a Developer account 

You'll need to create a [configuration file](/pleroma-bot/gettingstarted/configuration/) and obtain the [Fediverse tokens](/pleroma-bot/gettingstarted/beforerunning/#fediverse-tokens) for your accounts no matter what you choose to use.

## Guest tokens
If you prefer not [applying for a Twitter developer account](https://developer.twitter.com/en/apply-for-access) or want to get up and running as soon as possible, you can opt to use just Guest tokens.

The bot will automatically obtain them on its own when no `twitter_token` mapping is found [on your config file](/pleroma-bot/gettingstarted/configuration/#minimal-config).

It has certain limitations, however:

- Only gathers the latest 20 tweets for each account in every run
- No access to pinned status for tweets
- No access to tweets from protected accounts

To get started with Guest Tokens you'll just need to obtain the [Fediverse tokens](/pleroma-bot/gettingstarted/beforerunning/#fediverse-tokens) and create a [configuration file](/pleroma-bot/gettingstarted/configuration/).

## Twitter tokens

!!! info "Not needed if using an archive, an RSS feed or Guest Tokens"

To take full advantage of the bot, [applying for a Twitter developer account](https://developer.twitter.com/en/apply-for-access) is recommended.

The process involves some review of the developer account application by Twitter and it's very likely you'll be asked for some details pertaining your usecase. It usually doesn't take longer than a day or two to complete the application, the back and forth is mostly automated on their part.

Additionally, Twitter introduced a new tier of access (*Elevated*) to their API projects and although existing projects (before Nov 2021) were promoted automatically, new users will only get Essential access instead by default, in which requests to API v1.1 are disabled. 

We still use v1.1 for downloading videos and profile banners, and as of now there is no available alternative in v2.

So, you'll **need** [_***Elevated access***_](https://developer.twitter.com/en/docs/twitter-api/getting-started/about-twitter-api#v2-access-level) for the bot to function properly when using Twitter Tokens until further notice.

You can apply for Elevated access [here](https://developer.twitter.com/en/portal/products/elevated).

Once you have a Twitter developer account, you need to access your [dashboard](https://developer.twitter.com/en/portal/dashboard) and create a new project (so your app has v2 access) and also create a new app associated to that new project.

Now, enter your new application "Keys and tokens" section, copy and safely store all of your tokens.

![Keys and tokens](/pleroma-bot/images/keys.png)

* The [Bearer Token](https://developer.twitter.com/en/docs/authentication/api-reference/token) is usually enough for most usecases when running ```pleroma-bot```


However, if you plan on retrieving tweets from an account with **protected** tweets, you'll also need the following:

!!! warning "Keep in mind your Twitter developer account needs to **follow** or be the owner of the protected account for this to work"

* Consumer Key and Secret (or API key & secret)
* Access Token Key and Secret

Alternatively, you can obtain the Access Token and Secret by running [this](https://github.com/joestump/python-oauth2/wiki/Twitter-Three-legged-OAuth-Python-3.0) locally, while being logged in with a Twitter account which follows or is the owner of the protected account.

## Fediverse tokens

You will need to obtain the bearer tokens for the Fediverse account(s) you plan to use for mirroring.

=== "Mastodon"

    If you're using Mastodon, you can obtain a token by using the Web interface and navigating to `Settings -> Development`:
    ![Mastodon Token](/pleroma-bot/images/mastodon_web.png)
    * Scopes: ```read write```

    Save (and safely store) the value of the token generated for that Fediverse account, you'll need it in the next section.

=== "Misskey"

    If you're using [Misskey :octicons-link-external-24:](https://misskey-hub.net/en/docs/api#getting-an-access-token) you can obtain a token using the Web interface and navigating to `Settings -> API`:
    ![Misskey Token](/pleroma-bot/images/misskey_web.png)
    
    * Scopes:
        * View your account information
        * Edit your account information
        * Access your Drive files and folders
        * Edit or delete your Drive files and folders
        * Compose or delete notes
    
    Save (and safely store) the value of the token generated for that Fediverse account, you'll need it in the next section. 

=== "Pleroma"

    If you cannot get the token by using the Web interface (like in Pleroma instances), the alternative is to [follow the instructions on this site](https://tinysubversions.com/notes/mastodon-bot/) *while* being logged in as the Fediverse account, and enter:

    * Your server/instance URL (**without** *the protocol at the beginning, e.g. https://*)
    * The name of your app (doesn't really matter which one you choose, it's just a meaningful name so it's easy *for you* to identify)
    * Scopes: ```read write```


    When you're done with the last step (as in, running the cURL command):

    ```bash
    $ curl -F grant_type=authorization_code \
           -F redirect_uri=urn:ietf:wg:oauth:2.0:oob \ 
           -F client_id=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX \
           -F client_secret=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX \
           -F code=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX \
           -X POST https://yourinstance.fedi/oauth/token
    ```
    You'll get a response similar to this:
    ```json
    {
        "access_token":"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "created_at":99999999,
        "expires_in":99999,
        "me":"https://yourinstance.fedi/users/yourfediuser",
        "refresh_token":"ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
        "scope":"read write",
        "token_type":"Bearer"
    }
    ```

    Save the value of ```access_token```. *That* is the bearer token generated for that Fediverse account, you'll need it in the next section.