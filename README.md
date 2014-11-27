# GCalCron #

The goal of GCalCron is to use Google Calendar as a GUI to your crontab. It enables you to have at the same time:

 * clean and reliable scheduling thanks to the use of the Unix tool: `at`
 * a great user interface for quick and easy scheduling and re-scheduling using Google Calendar,
   available on all platforms, web and mobile.

A common use of this tool is to administer a home automation server.
Using GCalCron, changing your wake-up time before going to bed is as easy as changing the time of
the associated Google Calendar event.


## History ##

### NEW in version 3 ###

GCalCron 3 is a rewrite of the Google Calendar API part to make it compatible with Google API v3

### NEW in version 2.0 ###

GCalCron 2 is a complete rewrite of GCalCron by Patrick Spear.
See http://www.pfspear.net/projects/gcalcron for his first version.


## Features ##

 * Web+mobile GUI for cron-like scheduling
 * Tasks are stored in the description of the Google Calendar event
 * Fully compatible with Google Calendar recurrence settings
 * Scheduling based on 'at' for maximal reliability
 * GCal<->Cron syncs can be run at any given frequency, depending on your desired reactivity
 * Does not rely on permanent Internet connectivity thanks to the 7-days-ahead scheduling
 * Only the new and modified events are downloaded from Google at each run, for minimal bandwidth and latency
 * Timezone/DST aware, using datetutil.tz.gettz (new since 2012-01-16)
 * Simple settings file in JSON format
 * No Google password stored
 * DocTests! :-)


## Install ##

GCalCron depends on the google api python client library:

* `sudo pip install --upgrade google-api-python-client`

Clone the GCalCron repository:

```bash
git clone https://github.com/fabriceb/gcalcron.git $HOME/gcalcron
```

Run the script:

```bash
cd $HOME/gcalcron
python gcalcron.py
```

The first time it runs, it will need a client_secrets.json file. To get one, go to https://cloud.google.com/console#/project, create a new project and give it access to the Google Calendar API

If you havent already activated the consent screen in your console go to >API's & auth> Consent Screen. Ensure to select your email address at the top and give the product a name.

Then go in the APIs & auth > Credentials menu and hit the "Download JSON" in the OAuth "Client ID for native application" section. This will get you a file that you need to move inside the gcalcron folder and rename client_secrets.json

It will also need the id of the Google Calendar you intend to use for tasks scheduling.
If you create a dedicated calendar for this (recommended)
it will look like this: `1234567890abcdefghijklmnop@group.calendar.google.com`

Follow these instructions to find your Calendar ID:

 * In the calendar list on the left, click the down-arrow button next to the appropriate calendar,
   then select Calendar settings.
 * In the Calendar Address section, locate the Calendar ID listed next to the XML, ICAL and HTML buttons.

This has to be done only once, the OAuth login token is stored in a credentials.dat file and the Calendar ID in your settings file (default: $HOME/.gcalcron)

*Be aware that this OAuth login token gives read access to all your Google calendars! Please keep it in a safe place and do not use this program on a machine on which you are not the only root user!*

Add `python gcalcron.py` to your cron. Choose your desired sync frequency,
but it will only impact the delay between a change in Google Calendar and it being taken into account on your system.

For example, to sync every 10 minutes, run `crontab -e`, and add the following line:

```bash
PATH=/opt/bin:/bin:/usr/bin:/sbin:/usr/sbin
* * * * * python /your/home/directory/gcalcron/gcalcron.py
```

## Usage ##

 * In your Google Calendar, create a single or recurrent event, and list one command per line in the description.
 * Add `+10: ` or `-5: ` at the beginning of the line to add an offset of `+10` minutes or `-5` minutes to the command
 * Add `end: ` or `end -5: ` at the beginning of the line to add an offset relative to the end of the event
 * Example:

```bash
-60: /usr/bin/python /home/automation/heating_on.py
-10: /usr/bin/python /home/automation/boiler_on.py
-2: /usr/bin/python /home/automation/boiler_off.py
/usr/bin/php /root/phpdenon/wakeup.php
end: /usr/bin/python /home/automation/heating_off.py
```

## Development

To run DocTests: `python -m doctest -v gcalcron.py`

-------------------------------------------------------------------------

## Special section for LaCie Network Space 2 hackers ##

The LaCie Network Space 2 http://lacie.nas-central.org/wiki/Category:Network_Space_2 is a great-looking silent NAS. And most importantly it is easy to enable ssh, so it is a perfect choice for a discrete home automation solution.

I wrote GCalCron for such a device, here are the additional steps I needed to make it work:

 * Enable ssh on the machine: http://lacie.nas-central.org/wiki/Category:Network_Space_2#Enabling_SSH_with_disassembling
 * Install Ipkg, a lightweight package management system: http://forum.nas-central.org/viewtopic.php?f=236&t=2348 cs08q1armel worked perfectly for me

        cd /opt
        feed=http://ipkg.nslu2-linux.org/feeds/optware/cs08q1armel/cross/stable
        feednative=http://ipkg.nslu2-linux.org/feeds/optware/cs08q1armel/native/unstable
        ipk_name=`wget -qO- $feed/Packages | awk '/^Filename: ipkg-opt/ {print $2}'`
        wget $feed/$ipk_name
        tar -xOvzf $ipk_name ./data.tar.gz | tar -C / -xzvf -
        mkdir -p /opt/etc/ipkg
        echo "src cross $feed" > /opt/etc/ipkg/feeds.conf
        echo "src native $feednative" >> /opt/etc/ipkg/feeds.conf
        export PATH=/opt/bin:$PATH
        ipkg update

 * Install the `at` package

  * wget http://ipkg.nslu2-linux.org/feeds/optware/cs08q1armel/cross/stable/at_3.1.8-5_arm.ipk
  * ipkg at_3.1.8-5_arm.ipk


 * Install python-dateutil

  * wget http://labix.org/download/python-dateutil/python-dateutil-1.5.tar.gz
  * tar -xzvf python-dateutil-1.5.tar.gz
  * cd python-dateutil-1.5
  * python setup.py install
