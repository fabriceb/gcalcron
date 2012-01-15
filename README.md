# GCalCron2 #

The goal of GCalCron is to use Google Calendar as a GUI to your crontab. It enables you to have at the same time:

 * clean and reliable scheduling thanks to the use of the Unix tool: `at`
 * a great user interface for quick and easy scheduling and re-scheduling using Google Calendar,
   available on all platforms, web and mobile.

A common use of this tool is to administer a home automation server.
Using GCalCron2, changing your wake-up time before going to bed is as easy as changing the time of
the associated Google Calendar event.


## History ##

GCalCron2 is a complete rewrite of GCalCron by Patrick Spear.
See http://www.pfspear.net/projects/gcalcron for his first version.


## Features ##

 * Web+mobile GUI for cron-like scheduling
 * Tasks are stored in the description of the Google Calendar event
 * Fully compatible with Google Calendar recurrence settings
 * Scheduling based on 'at' for maximal reliability
 * GCal<->Cron syncs can be run at any given frequency, depending on your desired reactivity
 * Does not rely on permanent Internet connectivity thanks to the 7-days-ahead scheduling
 * Only the new and modified events are downloaded from Google at each run, for minimal bandwidth and latency
 * Timezone/DST aware (relies on time.altzone)
 * Simple settings file in JSON format
 * No Google password stored
 * DocTests! :-)


## Install ##

GcalCron2 depends on a few python libraries:

* Install on Ubuntu, Debian, etc. : `sudo apt-get install python-gdata python-dateutil`
* Install on Fedora, CentOS, etc. : `sudo yum install python-gdata python-dateutil`

Clone the GcalCron2 repository:

```bash
git clone https://github.com/fabriceb/GCalCron2.git $HOME/GCalCron2
```

Run the script:

```bash
cd $HOME/GCalCron2
python gcalcron2.py
```

The first time it runs, it will ask for your Google and Email password,
as well as the id of the Google Calendar you intend to use for tasks scheduling.
If you create a dedicated calendar for this (recommended)
it will look like this: `1234567890abcdefghijklmnop@group.calendar.google.com`

Follow these instructions to find your Calendar ID:

 * In the calendar list on the left, click the down-arrow button next to the appropriate calendar,
   then select Calendar settings.
 * In the Calendar Address section, locate the Calendar ID listed next to the XML, ICAL and HTML buttons.

This has to be done only once, the OAuth login token is then stored in your settings file (default: $HOME/.gcalcron2)

*Be aware that this OAuth login token gives read and write access to all your Google calendars! Please keep it in a safe place and do not use this program on a machine on which you are not the only root user!*

Add `python gcalcron2.py` to your cron. Choose your desired sync frequency,
but it will only impact the delay between a change in Google Calendar and it being taken into account on your system.

For example, to sync every 10 minutes, run `crontab -e`, and add the following line:

```bash
*/10 * * * * python /your/home/directory/GCalCron2/gcalcron2.py
```

## Usage ##

 * In your Google Calendar, create a single or recurrent event, and list one command per line in the description.
 * Add `+10: ` or `-5: ` at the beginning of the line to add an offset of `+10` minutes or `-5` minutes to the command


## Development

To run DocTests: `python -m doctest -v gcalcron2.py`

-------------------------------------------------------------------------

## Special section for LaCie Network Space 2 hackers ##

The LaCie Network Space 2 http://lacie.nas-central.org/wiki/Category:Network_Space_2 is a great-looking silent NAS. And most importantly it is easy to enable ssh, so it is a perfect choice for a discrete home automation solution.

I wrote GCalCron2 for such a device, here are the additional steps I needed to make it work:

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

 * Download the at package http://ipkg.nslu2-linux.org/feeds/optware/cs08q1armel/cross/stable/at_3.1.8-5_arm.ipk
 * install it: ipkg at_3.1.8-5_arm.ipk


