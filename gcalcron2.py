#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    gcalcron v2.0
#
#    Copyright Fabrice Bernhard 2011
#    fabriceb@theodo.fr
#    www.theodo.fr

import gdata.calendar.service
import os
import ConfigParser
import datetime


class Settings:
  application_name = 'theodo-gCalCron-2.0'
  settings_file = '.gcalcron2'
  login_token = None
  last_sync = None
  cal_id = None


  def get_file_path(self):
    return os.getenv('HOME') + '/' + self.settings_file


  def save(self):
    config = ConfigParser.RawConfigParser()
    config.add_section('GoogleCalendar')
    config.set('GoogleCalendar', 'login_token', self.login_token)
    config.set('GoogleCalendar', 'cal_id', self.cal_id)
    config.set('GoogleCalendar', 'time_zone', self.time_zone)
    config.add_section('GCalCron2')
    config.set('GCalCron2', 'last_sync', self.last_sync)
    with open(self.get_file_path(), 'wb') as configfile:
      config.write(configfile)
      #os.fchmod(configfile, 384) # 0600 rw for user only


  def load(self):
    config = ConfigParser.RawConfigParser()
    config.read(self.get_file_path())
    self.login_token = config.get('GoogleCalendar', 'login_token')
    self.last_sync   = config.get('GCalCron2', 'last_sync')
    self.cal_id      = config.get('GoogleCalendar', 'cal_id')
    self.time_zone   = config.get('GoogleCalendar', 'time_zone')


class GCalCron2:  
  client = None
  settings = None
  settings_params = ['login_token', 'cal_id', 'last_sync', 'time_zone']
  time_zone = 'Europe/Paris'


  def __init__(self):
    self.load_settings()


  def load_settings(self):
    self.settings = Settings()
    self.settings.load()
    for param in self.settings_params:
      value = getattr(self.settings, param)
      if value and value != '':
        setattr(self, param, value)


  def get_client(self):
    """
    Returns the Google Calendar API client
    @author Fabrice Bernhard
    @since 2011-06-13 
    """
    if not self.client:
      self.client = gdata.calendar.service.CalendarService()
      if self.settings.login_token:
        self.client.SetClientLoginToken(self.login_token)

    return self.client


  def fetch_login_token(self, email, password):
    """
    Fetches the Google Calendar API token using email and password
    @author Fabrice Bernhard
    @since 2011-06-13 
    """
    client = self.get_client()
    client.ClientLogin(email, password, source=self.application_name)

    return client.GetClientLoginToken()


  def get_events_to_sync(self, cal_id = 'default', last_sync = None, num_days = 7, verbose = True):
    """
    Gets a list of events to sync
     - events between now and last_sync + num_days which have been updated
     - new events between last_sync + num_days and now + num_days
    @author Fabrice Bernhard
    @since 2011-06-13 
    """

    start_date = datetime.datetime.now()
    end_date = start_date + datetime.timedelta(14);


    # Query the automation calendar.
    if verbose: print 'Setting up query: %s to %s' % (start_date, end_date,)
    query = gdata.calendar.service.CalendarEventQuery(cal_id, 'private', 'full')
    query.start_min = start_date.isoformat()
    query.start_max = end_date.isoformat()
    query.singleevents = 'true'
    query.ctz = self.time_zone
    query.max_results = 1000
    if last_sync:
      query.updated_min = last_sync.isoformat()
    if verbose: print 'Submitting query'
    feed = self.get_client().CalendarQuery(query)

    #return feed
    if verbose: print 'Query results received'

    for i, event in zip(xrange(len(feed.entry)), feed.entry):
      print event.title.text, event.when[0].start_time, '=>', datetime_to_at(iso_to_datetime(event.when[0].start_time))

    return feed


def iso_to_datetime(iso):
  return datetime.datetime.strptime(iso[:16], '%Y-%m-%dT%H:%M')


def datetime_to_at(dt):
  return dt.strftime('%H:%M %h %d %Y')