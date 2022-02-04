# Automate it

Great, now you're all ready to go, you have installed ```pleroma-bot``` and created a config for your needs. But where's the fun in all of that if you have to run it manually everytime, right?

## Daemon mode

`pleroma-bot` can run in the background by launching it in daemon mode:
```console
$ pleroma-bot -d
```
By default, it will re-run every 60 minutes. You can override this behaviour with `--pollrate` or `-p`.
This will run it every 15 minutes:
```bash
$ pleroma-bot -d -p 15
```

## Systemd service

The [AUR package :material-arch:](https://aur.archlinux.org/packages/python-pleroma-bot) will automatically install the systemd service `pleroma-bot.service`. 

If you installed `pleroma-bot` by other methods, you will have to manually install it:

???+ note "The `pleroma-bot.service` file can be found at the root of the code repository"

    ```cfg
    [Unit]
    Description=Stork (pleroma-bot)
    Documentation=https://robertoszek.github.io/pleroma-bot
    After=network.target

    [Service]
    Environment=PYTHONUNBUFFERED=1
    # Uncomment this line if using venv
    # ExecStart=/path/to/venv/bin/pleroma-bot -d --config /etc/pleroma-bot/config.yml --log /var/log/pleroma-bot/error.log --skipChecks
    ExecStart=pleroma-bot -d --config /etc/pleroma-bot/config.yml --log /var/log/pleroma-bot/error.log --skipChecks
    ```
    
!!! warning "If you're using a [virtual environment :octicons-file-code-24:](https://docs.python.org/3/tutorial/venv.html) you may have to edit the service file first"

=== "System-level"

    ```console
    $ sudo cp pleroma-bot.service /etc/systemd/system/pleroma-bot.service
    $ sudo systemctl daemon-reload
    $ sudo systemctl start pleroma-bot
    ```

=== "User-level"

    ```console
    $ cp pleroma-bot.service ~/.config/systemd/user/pleroma-bot.service
    $ systemctl --user daemon-reload
    $ systemctl --user start pleroma-bot
    ```



## Skip first run checks

It's worth noting that ```pleroma-bot``` accepts the flag ```--skipChecks```, which will ignore all of the first run checks (e.g. no user folder found, no posts/toots in the target Fediverse account, etc). Most importantly, if you pass this argument you can rest assured no input will be asked during the run. Which makes it perfect for our purposes of running it on a timer with no manual intervention.

```console
$ pleroma-bot --skipChecks
```

## Run on a timer

If you prefer not using the daemon mode, you can instead opt to run `pleroma-bot` on a timer of your choosing. 

### Cron

Fan favourite and well-known. 
If you have trouble figuring out cron schedule expressions, you can use this [site](https://crontab.guru/) to analyze them.

First, start by editing your current crontab:

```console
$ crontab -e
```

In our example, we'll add some lines at the end of the crontab, which will:

* Post new tweets **(every 10 min.)**
* Update profile info **(everyday at 6:15 AM)**


=== "Using PyPi"
    !!! info "Feel free to omit "```1> /dev/null```" Its main use here is to drop any output from the standard output, in case you have configured cron to send you emails if any commands generate output"

    * System-wide:

    ```bash
    # Post tweets every 10 min
    */10 * * * * pleroma-bot --noProfile --skipChecks -c /path/to/config.yml -l /path/to/error.log 1> /dev/null

    # Update pleroma profile with Twitter info every day at 6:15 AM
    15 6 * * * pleroma-bot --skipChecks -c /path/to/config.yml 1> /dev/null
    ```

    * Or if you're using a [virtual environment :octicons-file-code-24:](https://docs.python.org/3/tutorial/venv.html):

    ```bash
    # Post tweets every 10 min
    */10 * * * * cd /path/to/your/venv/ && . bin/activate && pleroma-bot --noProfile --skipChecks -c /path/to/config.yml -l /path/to/error.log

    # Update pleroma profile with Twitter info every day at 6:15 AM
    15 6 * * * cd /path/to/your/venv/ && . bin/activate && pleroma-bot --skipChecks -c /path/to/config.yml -l /path/to/error.log
    ```
    

=== "Using AUR package"
    !!! info "You can freely omit ```1> /dev/null```. Its main use here is to drop any output from the standard output, in case you have configured cron to send you emails if any commands generate output"

    ```bash
    # Post tweets every 10 min
    */10 * * * * pleroma-bot --noProfile --skipChecks -c /path/to/config.yml -l /path/to/error.log

    # Update pleroma profile with Twitter info every day at 6:15 AM
    15 6 * * * pleroma-bot --skipChecks -c /path/to/config.yml -l /path/to/error.log
    ```

=== "Using Git"
    !!! info "You can freely omit ```1> /dev/null```. Its main use here is to drop any output from the standard output, in case you have configured cron to send you emails if any commands generate output"

    ```bash
    # Post tweets every 10 min
    */10 * * * * cd /path/to/cloned/repo/ && python3 -m pleroma_bot.cli --noProfile --skipChecks -c /path/to/config.yml -l /path/to/error.log

    # Update pleroma profile with Twitter info every day at 6:15 AM
    15 6 * * * cd /path/to/cloned/repo/ && python3 -m pleroma_bot.cli --skipChecks -c /path/to/config.yml -l /path/to/error.log
    ```

### Systemd timers

You can achieve the same results with [Systemd timers](https://www.freedesktop.org/software/systemd/man/systemd.timer.html). The choice of which one to use (cron or systemd timers) it's really up to you, basically which one fits more your needs.

Create a service file with the following content:

```bash title="/etc/systemd/system/pleroma-bot@.service"
[Unit]
Description=Bot that mirrors Twitter accounts on the Fediverse

[Service]
Type=oneshot
ExecStart=/usr/bin/pleroma-bot --skipChecks -c /path/to/config.yml -l /path/to/error.log %i
```

Also, create 2 timer files with the following content:

```bash title="/etc/systemd/system/pleroma-bot-tweets.timer"
[Unit]
Description=Run pleroma-bot every 10min

[Timer]
Unit=pleroma-bot@.service
OnCalendar=*:0/10
Persistent=true

[Install]
WantedBy=timers.target
```

```bash title="/etc/systemd/system/pleroma-bot-profile.timer"
[Unit]
Description=Run pleroma-bot with noProfile at 6:15am

[Timer]
Unit=pleroma-bot@noProfile.service
OnCalendar=*-*-* 6:15:00
Persistent=true

[Install]
WantedBy=timers.target
```
Enable and start the timers:
```console
# systemctl enable pleroma-bot-profile.timer
# systemctl --user start pleroma-bot-profile.timer
# systemctl enable pleroma-bot-tweets.timer
# systemctl --user start pleroma-bot-tweets.timer
```