#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    gcalcron v2.1
#
#    Copyright Fabrice Bernhard 2011-2013
#    fabriceb@theodo.fr
#    www.theodo.fr

"""Command-line synchronisation application between Google Calendar and Linux's Crontab.
Usage:
  $ python gcalcron2.py
"""

# Google API
import argparse
import httplib2
import os
import sys
from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools

# GCalCron
import json
import datetime
import dateutil.parser
from dateutil.tz import gettz
import time
import subprocess
import re
import logging

logger = logging.getLogger(__name__)

# Parser for command-line arguments.
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[tools.argparser])
parser.add_argument('--reset', default=False,
                        help='Reset all synchronised events')




class GCalAdapter:
  """
  Adapter class which communicates with the Google Calendar API
  @since 2011-06-19
  """

  # CLIENT_SECRETS is name of a file containing the OAuth 2.0 information for this
  # application, including client_id and client_secret. You can see the Client ID
  # and Client secret on the APIs page in the Cloud Console:
  # <https://cloud.google.com/console#/project/395452703880/apiui>
  CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')


  def __init__(self, calendarId=None, flags=None):
    self.calendarId = calendarId
    self.service = None

  def get_service(self):
    if not self.service:
      # If the credentials don't exist or are invalid run through the native client
      # flow. The Storage object will ensure that if successful the good
      # credentials will get written back to the file.
      storage = file.Storage(os.path.join(os.path.dirname(__file__), 'credentials.dat'))
      credentials = storage.get()
      if credentials is None or credentials.invalid:
        # Set up a Flow object to be used for authentication.
        # Add one or more of the following scopes. PLEASE ONLY ADD THE SCOPES YOU
        # NEED. For more information on using scopes please see
        # <https://developers.google.com/+/best-practices>.
        FLOW = client.flow_from_clientsecrets(self.CLIENT_SECRETS,
          scope=[
              'https://www.googleapis.com/auth/calendar.readonly',
            ],
          message=tools.message_if_missing(self.CLIENT_SECRETS))

        credentials = tools.run_flow(FLOW, storage, flags)


      # Create an httplib2.Http object to handle our HTTP requests and authorize it
      # with our good Credentials.
      http = httplib2.Http()
      http = credentials.authorize(http)
      # Construct the service object for the interacting with the Calendar API.
      self.service = discovery.build('calendar', 'v3', http=http)

    return self.service

  def get_query(self, start_min, start_max, updated_min=None):
    """
    Builds the Google Calendar query with default options set

    >>> g = GCalAdapter()
    >>> g.get_query(datetime.datetime(2011, 6, 19, 14, 0), datetime.datetime(2011, 6, 26, 14, 0), datetime.datetime(2011, 6, 18, 14, 0))
    {'orderBy': 'updated', 'showDeleted': True, 'calendarId': None, 'timeMin': '2011-06-19T14:00:00', 'updatedMin': '2011-06-18T14:00:00', 'timeMax': '2011-06-26T14:00:00', 'fields': 'items(description,end,id,start,status,summary,updated)', 'singleEvents': True, 'maxResults': 1000}

    @author Fabrice Bernhard
    @since 2011-06-19
    """

    logger.info('Setting up query: %s to %s modified after %s' % (start_min.isoformat(), start_max.isoformat(), updated_min))

    query = {
      'calendarId': self.calendarId,
      'maxResults': 1000,
      'orderBy': 'updated',
      'showDeleted': True,
      'singleEvents': True,
      'fields': 'items(description,end,id,start,status,summary,updated)',
      'timeMin': start_min.isoformat(),
      'timeMax': start_max.isoformat(),
    }

    if updated_min:
      query['updatedMin'] = updated_min.isoformat()

    return query

  def queryApi(self, queries):
    """Query the Google Calendar API."""

    logger.info('Submitting query')

    entries = []
    for query in queries:
      try:
        pageToken = None
        while True:
          query['pageToken'] = pageToken
          gCalEvents = self.get_service().events().list(**query).execute()
          entries += gCalEvents['items']
          pageToken = gCalEvents.get('nextPageToken')
          if not pageToken:
            break
      except client.AccessTokenRefreshError:
        print ("The credentials have been revoked or expired, please re-run"
          "the application to re-authorize")

    logger.info('Query results received')
    logger.debug(entries)

    return entries

  def get_events(self, sync_start, last_sync = None, num_days = datetime.timedelta(days=7)):
    """
    Gets a list of events to sync
     - events between sync_start and last_sync + num_days which have been updated since last_sync
     - new events between last_sync + num_days and sync_start + num_days
    @author Fabrice Bernhard
    @since 2011-06-13
    """

    queries = []
    end = sync_start + num_days
    if last_sync:
      # query all events modified since last synchronisation
      queries.append(self.get_query(sync_start, last_sync + num_days, last_sync))
      # query all events which appeared in the [last_sync + num_days, sync_start + num_days] time frame 
      queries.append(self.get_query(last_sync + num_days, end))
    else:
      queries.append(self.get_query(sync_start, end))

    return self.queryApi(queries)


class GCalCron:
  """
  Schedule your cron commands in a dedicated Google Calendar,
  this class will convert them into UNIX "at" job list and keep
  them synchronised in case of updates

  @author Fabrice Bernhard
  @since 2011-06-13
  """

  settings = None
  settings_file = os.getenv('HOME') + '/' + '.gcalcron2'


  def __init__(self, gCalAdapter=None):
    self.gCalAdapter = gCalAdapter
    self.load_settings()


  def load_settings(self):
    try:
      with open(self.settings_file) as f:
        self.settings = json.load(f)
    except IOError:
      calendarId = raw_input('Calendar id (in the form of XXXXX....XXXX@group.calendar.google.com or for the main one just your Google email): ')
      self.init_settings(calendarId)
      self.save_settings()

  def save_settings(self):
    with open(self.settings_file, 'w') as f:
      json.dump(self.settings, f, indent=2)


  def init_settings(self, calendarId):
    self.settings = {
      "jobs": {},
      "calendarId": calendarId,
      "last_sync": None
    }

  def getCalendarId(self):
    return self.settings["calendarId"]


  def clean_settings(self):
    """Cleans the settings from saved jobs in the past"""

    for event_uid, job in self.settings['jobs'].items():
      if datetime.datetime.strptime(job['date'], '%Y-%m-%d') <= datetime.datetime.now() - datetime.timedelta(days=1):
        del self.settings['jobs'][event_uid]

  def reset_settings(self):
    for event, job in self.settings['jobs'].items():
      command = [u'at', u'-d'] + job['ids']
      logger.debug(command)
      p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      (stdout, stderr) = p.communicate()
      logger.debug(stdout)
      logger.debug(stderr)
    self.settings['last_sync'] = None
    self.settings['jobs'] = {}
    self.save_settings()


  def unschedule_old_jobs(self, events):
    removed_job_ids = []
    for event in events:
      if event['uid'] in self.settings['jobs']:
        removed_job_ids += self.settings['jobs'][event['uid']]['ids']
        del self.settings['jobs'][event['uid']]
    if len(removed_job_ids) > 0:
      command = [u'at', u'-d'] + removed_job_ids
      logger.debug(command)
      p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      (stdout, stderr) = p.communicate()
      logger.debug(stdout)
      logger.debug(stderr)

  def schedule_new_jobs(self, events):
    for event in events:
      if not 'commands' in event:
        continue

      for command in event['commands']:
        if command['exec_time'] <= datetime.datetime.now():
          continue

        cmd = ['at', datetime_to_at(command['exec_time'])]
        logger.debug(cmd)

        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdout, stderr) = p.communicate(command['command'])

        logger.debug(stdout)
        logger.debug(stderr)

        job_id_match = re.compile('job (\d+) at').search(stderr)

        if job_id_match:
          job_id = job_id_match.group(1)
        logger.debug('identified job_id: ' + job_id)

        if event['uid'] in self.settings['jobs']:
          self.settings['jobs'][event['uid']]['ids'].append(job_id)
        else:
          self.settings['jobs'][event['uid']] = {
            'date': command['exec_time'].strftime('%Y-%m-%d'),
            'ids': [job_id, ]
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
      last_sync = dateutil.parser.parse(self.settings['last_sync'])

    sync_start = datetime.datetime.now(gettz())
    events = self.gCalAdapter.get_events(sync_start, last_sync, num_days)
    commandsList = parse_events(events)

    # first unschedule all modified/deleted events
    self.unschedule_old_jobs(commandsList)

    # then reschedule all modified/new events
    self.schedule_new_jobs(commandsList)

    # clean old jobs from the settings
    self.clean_settings()

    self.settings['last_sync'] = str(sync_start)
    self.save_settings()


def parse_commands(event_description, start_time, end_time):
  """
  Parses the description of a Google calendar event and returns a list of commands to execute

  >>> parse_commands("echo 'Wake up!'\\n+10: echo 'Wake up, you are 10 minutes late!'", datetime.datetime(3011, 6, 19, 8, 30), datetime.datetime(3011, 6, 19, 9, 0))
  [{'exec_time': datetime.datetime(3011, 6, 19, 8, 30), 'command': "echo 'Wake up!'"}, {'exec_time': datetime.datetime(3011, 6, 19, 8, 40), 'command': "echo 'Wake up, you are 10 minutes late!'"}]

  >>> parse_commands("Turn on lights\\nend -10: Dim lights\\nend: Turn off lights", datetime.datetime(3011, 6, 19, 18, 30), datetime.datetime(3011, 6, 19, 23, 0))
  [{'exec_time': datetime.datetime(3011, 6, 19, 18, 30), 'command': 'Turn on lights'}, {'exec_time': datetime.datetime(3011, 6, 19, 22, 50), 'command': 'Dim lights'}, {'exec_time': datetime.datetime(3011, 6, 19, 23, 0), 'command': 'Turn off lights'}]


  @author Fabrice Bernhard
  @since 2011-06-13
  """

  commands = []
  for command in event_description.split("\n"):
    exec_time = start_time
    # Supported syntax for offset prefixes:
    #   '[+-]10: ', 'end:', 'end[+-]10:', 'end [+-]10:'
    offset_match = re.compile('^(end)? ?([\+,-]\d+)?: (.*)').search(command)
    if offset_match:
      if offset_match.group(1):
        exec_time = end_time
      if offset_match.group(2):
        exec_time += datetime.timedelta(minutes=int(offset_match.group(2)))
      command = offset_match.group(3)

    command = command.strip()
    if command:
      if exec_time >= datetime.datetime.now():
        commands.append({
            'command': command,
            'exec_time': exec_time
          })
      else:
        logger.debug('Ignoring command that was scheduled for the past')
    else:
      logger.debug('Blank command')

  return commands

def parse_events(events):
  """
  Transforms the Google Calendar API results into a list of commands

  >>> parse_events([{u'status': u'confirmed', u'updated': u'2013-12-22T19:49:13.750Z', u'end': {u'dateTime': u'2113-12-23T02:00:00+01:00'}, u'description': u'-60: start_heating.py\\n0: turn_music_on.py\\n+30: stop_heating.py', u'summary': u'Wakeup', u'start': {u'dateTime': u'2113-12-23T01:00:00+01:00'}, u'id': u'olbia2urfm1ns0h88v4u0d9a5g'}])
  [{'commands': [{'exec_time': datetime.datetime(2113, 12, 23, 0, 0), 'command': u'start_heating.py'}, {'exec_time': datetime.datetime(2113, 12, 23, 1, 0), 'command': u'0: turn_music_on.py'}, {'exec_time': datetime.datetime(2113, 12, 23, 1, 30), 'command': u'stop_heating.py'}], 'uid': u'olbia2urfm1ns0h88v4u0d9a5g'}]

  >>> parse_events([{u'status': u'cancelled', u'updated': u'2013-12-22T19:52:50.525Z', u'end': {u'dateTime': u'2013-12-23T02:00:00+01:00'}, u'description': u'-60: start_heating.py\\n0: turn_music_on.py\\n+30: stop_heating.py', u'summary': u'Wakeup', u'start': {u'dateTime': u'2013-12-23T01:00:00+01:00'}, u'id': u'olbia2urfm1ns0h88v4u0d9a5g'}])
  [{'uid': u'olbia2urfm1ns0h88v4u0d9a5g'}]

  @author Fabrice Bernhard
  @since 2013-12-22
  """
  commandsList = []
  for event in events:
    start_time = dateutil.parser.parse(event['start']['dateTime']).replace(tzinfo=None)
    end_time   = dateutil.parser.parse(event['end']['dateTime']).replace(tzinfo=None)
    event_description = ''
    if 'description' in event:
      event_description = event['description']
    logger.debug(event['id'] + '-' + event['status'] + '-' + event['updated'] + ': ' + unicode(start_time) + ' -> ' + unicode(end_time) + ' (' + event['start']['dateTime'] + ' -> ' + event['end']['dateTime'] + ') ' + '=>' + event_description)
    if event['status'] == 'cancelled':
      logger.info("cancelled " + event['id'])
      commandsList.append({
        'uid': event['id']
      })
    elif event_description:
      commands = parse_commands(event_description, start_time, end_time)
      if commands:
        commandsList.append({
            'uid': event['id'],
            'commands': commands
          })

  logger.debug(commandsList)

  return commandsList

def datetime_to_at(dt):
  """
  >>> datetime_to_at(datetime.datetime(2011, 6, 18, 12, 0))
  '12:00 Jun 18'
  """
  return dt.strftime('%H:%M %h %d')



def main(argv):
  # Parse the command-line flags.
  flags = parser.parse_args(argv[1:])

  level = getattr(logging, flags.logging_level)
  logger.setLevel(logging.DEBUG)
  h1 = logging.StreamHandler(sys.stdout)
  h1.setLevel(level)
  logger.addHandler(h1)

  fh = logging.FileHandler(os.path.join(os.path.dirname(__file__), 'gcalcron.log'))
  fh.setLevel(logging.DEBUG)
  logger.addHandler(fh)

  try:
    g = GCalCron()
    gCalAdapter = GCalAdapter(g.getCalendarId(), flags)
    g.gCalAdapter = gCalAdapter

    if flags.reset:
      g.reset_settings()
    else:
      g.sync_gcal_to_cron()
      logger.info('Sync succeeded')
  except:
    logging.exception('Sync failed')

if __name__ == '__main__':
  main(sys.argv)

