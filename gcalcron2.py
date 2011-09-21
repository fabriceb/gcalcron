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
import stat
import json
import datetime
import time
import subprocess
import re

DEBUG = False

class GCalAdapter:
  """
  Adapter class which communicates with the Google Calendar API
  @since 2011-06-19
  """

  application_name = 'Theodo-gCalCron-2.0'  
  client = None
  cal_id = None
  login_token = None


  def __init__(self, cal_id=None, login_token=None):
    self.cal_id = cal_id
    self.login_token = login_token


  def get_client(self):
    """
    Returns the Google Calendar API client
    @author Fabrice Bernhard
    @since 2011-06-13 
    """

    if not self.client:
      self.client = gdata.calendar.service.CalendarService()
      if self.login_token:
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


  def get_query(self, start_min, start_max, updated_min=None):
    """
    Builds the Google Calendar query with default options set

    >>> g = GCalAdapter()
    >>> g.cal_id = 'login@gmail.com'
    >>> g.get_query(datetime.datetime(2011, 6, 19, 14, 0), datetime.datetime(2011, 6, 26, 14, 0), datetime.datetime(2011, 6, 18, 14, 0))
    {'start-max': '2011-06-26T12:00:00', 'max-results': '1000', 'singleevents': 'true', 'updated-min': '2011-06-18T12:00:00', 'start-min': '2011-06-19T12:00:00'}
    
    @author Fabrice Bernhard
    @since 2011-06-19
    """

    if DEBUG: print 'Setting up query: %s to %s modified after %s' % (start_min, start_max, updated_min)
    
    query = gdata.calendar.service.CalendarEventQuery(self.cal_id, 'private', 'full')
    query.start_min = local_to_utc(start_min).isoformat()
    query.start_max = local_to_utc(start_max).isoformat()
    query.singleevents = 'true'
    query.ctz = 'UTC'
    query.max_results = 1000
    if updated_min:
      query.updated_min = local_to_utc(updated_min).isoformat()

    return query


  def get_events(self, last_sync = None, num_days = datetime.timedelta(days=7)):
    """
    Gets a list of events to sync
     - events between now and last_sync + num_days which have been updated since last_sync
     - new events between last_sync + num_days and now + num_days
    @author Fabrice Bernhard
    @since 2011-06-13 
    """

    queries = []
    entries = []
    now = datetime.datetime.now()
    if last_sync:
      queries.append(self.get_query(now, last_sync + num_days, last_sync))
      queries.append(self.get_query(last_sync + num_days, now + num_days))
    else:
      queries.append(self.get_query(datetime.datetime.now(), datetime.datetime.now() + num_days))

    # Query the automation calendar.
    if DEBUG: print 'Submitting query'
    for query in queries:
      feed = self.get_client().CalendarQuery(query)
      if len(feed.entry) > 0:
        entries += feed.entry

    if DEBUG: print 'Query results received'

    events = []
    for i, event in zip(xrange(len(entries)), entries):
      event_time = utc_to_local(iso_to_datetime(event.when[0].start_time))
      event_id = event.id.text
      if DEBUG: print event_id, '-', event.event_status.value, '-', event.updated.text, ': ', event.title.text, event_time, ' (', event.when[0].start_time, ') ', '=>', event.content.text
      if event.content.text:
        commands = self.parse_commands(event.content.text, event_time)
        events.append({
            'uid': event_id,
            'commands': commands
          })

      elif event.event_status.value == 'CANCELED':
        if DEBUG: print "CANCELLED", event_id
        events.append({
          'uid': event_id
        })

    if DEBUG: print events

    return (events, now)

  def parse_commands(self, event_description, event_time):
    """
    Parses the description of a Google calendar event and returns a list of commands to execute

    >>> g = GCalAdapter()
    >>> g.parse_commands("echo 'Wake up!'\\n+10: echo 'Wake up, you are 10 minutes late!'", datetime.datetime(2011, 6, 19, 8, 30))
    [{'exec_time': datetime.datetime(2011, 6, 19, 8, 30), 'command': "echo 'Wake up!'"}, {'exec_time': datetime.datetime(2011, 6, 19, 8, 40), 'command': "echo 'Wake up, you are 10 minutes late!'"}]

    @author Fabrice Bernhard
    @since 2011-06-13 
    """

    commands = []
    for command in event_description.split("\n"):
      exec_time = event_time
      offset_match = re.compile('([\+,-]\d+): (.*)').search(command)
      if offset_match:
        exec_time += datetime.timedelta(minutes=int(offset_match.group(1)))
        command = offset_match.group(2)
      commands.append({
          'command': command,
          'exec_time': exec_time
        })

    return commands


class GCalCron2:
  """
  Schedule your cron commands in a dedicated Google Calendar,
  this class will convert them into UNIX "at" job list and keep
  them synchronised in case of updates

  @author Fabrice Bernhard
  @since 2011-06-13 
  """
  
  settings = None
  settings_file = os.getenv('HOME') + '/' + '.gcalcron2'

  def __init__(self, load_settings=True):
    if load_settings:
      self.load_settings()


  def load_settings(self):
    with open(self.settings_file) as f:
      self.settings = json.load(f)

  def save_settings(self):
    with open(self.settings_file, 'w') as f:
      json.dump(self.settings, f, indent=2)
    # protect the settings fie, since it contains the OAuth login token
    os.chmod(self.settings_file, stat.S_IRUSR + stat.S_IWUSR)

  def init_settings(self, email, password, cal_id):
    gcal_adapter = GCalAdapter()
    login_token = gcal_adapter.fetch_login_token(email, password)
    self.settings = {
      "jobs": {}, 
      "google_calendar": {
        "login_token": login_token, 
        "cal_id": cal_id
      }, 
      "last_sync": None
    }


  def sync_gcal_to_cron(self, num_days = datetime.timedelta(days=7), verbose = True):
    """
    - fetches a list of commands through the GoogleCalendar adapter
    - schedules them for execution using the unix "at" command
    - stores their job_id in case of later modifications
    - deletes eventual cancelled jobs

    @author Fabrice Bernhard
    @since 2011-06-13 
    """

    last_sync = None
    if self.settings['last_sync']:
      last_sync = datetime.datetime.strptime(self.settings['last_sync'][:16], '%Y-%m-%d %H:%M')

    gcal_adapter = GCalAdapter(self.settings['google_calendar']['cal_id'], self.settings['google_calendar']['login_token'])

    (events, last_sync) = gcal_adapter.get_events(last_sync, num_days)

    # if event was modified or cancelled, erase existing jobs
    job_ids = []
    for event in events:  
      if event['uid'] in self.settings['jobs']:
        job_ids += self.settings['jobs'][event['uid']]['ids']
        del self.settings['jobs'][event['uid']]
    if len(job_ids) > 0:
      if DEBUG: print ' '.join(['at', '-d'] + job_ids)
      p = subprocess.Popen(['at', '-d'] + job_ids)

    for event in events:
      if 'commands' in event:
        for command in event['commands']:
          if DEBUG: print "at "+ datetime_to_at(command['exec_time']) 
          p = subprocess.Popen(['at', datetime_to_at(command['exec_time'])], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
          (_, output) = p.communicate(command['command'])
          if DEBUG: print "  " + output
          job_id = re.compile('job (\d+) at').search(output).group(1)
          if event['uid'] in self.settings['jobs']:
            self.settings['jobs'][event['uid']]['ids'].append(job_id)
          else:
            self.settings['jobs'][event['uid']] = {
              'date': command['exec_time'].strftime('%Y-%m-%d'),
              'ids': [job_id, ]
            }

    
    # clean the jobs in the file
    event_uids = self.settings['jobs'].keys()
    for event_uid in event_uids:
      if datetime.datetime.strptime(self.settings['jobs'][event_uid]['date'], '%Y-%m-%d') <= datetime.datetime.now() - datetime.timedelta(days=1):
        del self.settings['jobs'][event_uid]

    self.settings['last_sync'] = str(last_sync)
    self.save_settings()


def local_to_utc(dt):
  return dt + datetime.timedelta(seconds=time.altzone)

def utc_to_local(dt):
  return dt - datetime.timedelta(seconds=time.altzone)

def iso_to_datetime(iso):
  """
  >>> iso_to_datetime('2011-06-18T12:00:00')
  datetime.datetime(2011, 6, 18, 12, 0)
  """
  return datetime.datetime.strptime(iso[:16], '%Y-%m-%dT%H:%M')


def datetime_to_at(dt):
  """
  >>> datetime_to_at(datetime.datetime(2011, 6, 18, 12, 0))
  '12:00 Jun 18'
  """
  return dt.strftime('%H:%M %h %d')


if __name__ == '__main__':
  try:
    g = GCalCron2()
  except IOError:
    email = raw_input('Google email: ')
    password = raw_input('Google password: ')
    cal_id = raw_input('Calendar id (in the form of XXXXX....XXXX@group.calendar.google.com or for the main one just your Google email): ')
    g = GCalCron2(load_settings=False)
    g.init_settings(email, password, cal_id)
  g.sync_gcal_to_cron()