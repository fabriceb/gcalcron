# GCalCron2 #

The goal of GCalCron is to use Google Calendar as a GUI to your crontab. It enable you to have at the same time:
 - clean and reliable scheduling thanks to the use of the Unix tool: at
 - a great user interface for quick and easy scheduling and re-scheduling using Google Calendar, available on all platforms, web and mobile.

A common use of this tool is to administer a home automation server. Using GCalCron2, changing your wake-up time before going to bed is as easy as changing the time of the associated Google Calendar event


## History ##

GCalCron2 is a complete rewrite of GCalCron by Patrick Spear. See http://www.pfspear.net/projects/gcalcron for hist first version


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

On Ubuntu 10.10 and later :

sudo apt-get install python-gdata
python gcalcron2.py

The first time, it will ask for your Google and Email password, as well as the id of the Google Calendar you intend to use for tasks scheduling. If you create a dedicated calendar for this (recommended) it will look like this: 1234567890abcdefghijklmnop@group.calendar.google.com

Follow these instructions to find your Calendar ID:
 * In the calendar list on the left, click the down-arrow button next to the appropriate calendar, then select Calendar settings.
 * In the Calendar Address section, locate the Calendar ID listed next to the XML, ICAL and HTML buttons.

This has to be done only once, the OAuth login token is then stored in your settings file, by default .gcalcron2 in your HOME directory

'''Be aware that this OAuth login token gives read and write access to all your Google calendars! Please keep it in a safe place and do not use this program on a machine on which you are not the only root user!'''

Add "python gcalcron2.py" to your cron. Choose the frequency that suits your needs, it will only impact the delay between a change in Google Calendar and it being taken into account on your system.


## Usage ##

 * In your Google Calendar, create a single or recurrent event and list one command per line in the description
 * Add "+10: " or "-5: " at the beginning of the line to add an offset of +10 minutes or -5 minutes to the command