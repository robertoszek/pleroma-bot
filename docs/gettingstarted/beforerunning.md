# Before running

If you haven't already, you need to [apply for a Twitter developer account](https://developer.twitter.com/en/apply-for-access).

The process involves some review of the developer account application by Twitter and it's very likely you'll be asked for some details pertaining your usecase. It usually doesn't take longer than a day or two to complete the application, the back and forth is mostly automated on their part.

Additionally, Twitter introduced a new tier of access (Elevated) to their API projects and although existing projects (before Nov 2020) were promoted automatically, new users will only get Essential access instead by default, in which requests to API v1.1 are disabled. 

We still use v1.1 for downloading videos and profile banners, and as of now there is no available alternative in v2, so you'll need Elevated access for the bot to function properly until further notice.

You can apply for Elevated access [here](https://developer.twitter.com/en/portal/products/elevated).

## Twitter tokens

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

You also need to obtain the bearer tokens for the Fediverse account(s) you plan to use for mirroring.

*While* being logged in as the Fediverse account, [follow the instructions on this site](https://tinysubversions.com/notes/mastodon-bot/) and enter:

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