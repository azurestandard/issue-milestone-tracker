import re
import sqlite3

from dateutil.parser import parse
from pytz import timezone
from util.github import GitHub


class Event:
    def __init__(self, row):
        pacific = timezone('US/Pacific')

        self.event_id = row[0]
        self.fullname = row[1]
        self.created_at = parse(row[2]).astimezone(pacific)
        self.created_date = '{:%m/%d/%Y}'.format(self.created_at)
        self.created_time = '{:%I:%M%p}'.format(self.created_at)
        self.month = row[3]
        self.day = row[4]
        self.year = row[5]
        self.time = row[6]
        self.source = row[7]
        self.source_id = row[8]
        self.repo = row[9]
        self.event = row[10]
        self.payload_id = row[11]
        self.action = row[12]
        self.url = row[13]
        self.title = row[14]

        def __unicode__(self):
            return '{}: {}'.format(self.event_id, self.title)


class Database:
    def __init__(self, conn, cur):
        self.conn = conn
        self.cur = cur

    def build(self):
        self.cur.execute('CREATE TABLE IF NOT EXISTS user '
                         '('
                         'user_id INTEGER PRIMARY KEY, '
                         'first_name TEXT, '
                         'last_name TEXT, '
                         'github TEXT'
                         ')')
        self.cur.execute('CREATE TABLE IF NOT EXISTS event '
                         '('
                         'event_id INTEGER PRIMARY KEY, '
                         'user_id INTEGER, '
                         'created_at TEXT, '
                         'source TEXT, '
                         'source_id TEXT, '
                         'repo TEXT, '
                         'event TEXT, '
                         'payload_id TEXT, '
                         'action TEXT, '
                         'url TEXT, '
                         'title TEXT'
                         ')')

    def populate(self, organization, username, password, timezone):
        github = GitHub(username, password, timezone)

        # Get our organization
        org = github.get_org(organization)

        # Get a list of repositories in the organization
        repos = github.get_repos(org)
        repos = sorted(repos, key=lambda k: k['name'])

        for repo in repos:
            events = github.get_repo_events(organization,
                                            repo['name'])
            if events:
                for event in events:
                    # Does the user already exist?
                    self.cur.execute('SELECT user_id FROM user WHERE github = ?', (event['actor']['login'], ))
                    row = self.cur.fetchone()

                    user_id = None
                    if row == None:
                        self.cur.execute('INSERT INTO user(github) VALUES(?)', (event['actor']['login'], ))
                        user_id = self.cur.lastrowid
                        self.conn.commit()
                    else:
                        user_id = row[0]

                    type = re.sub('([A-Z])', r' \1', event['type']).lstrip(' ')[:-6]
                    if type == 'Gollum':
                        type = 'Wiki'

                    payload_id = None
                    if 'payload' in event:
                        if 'number' in event['payload']:
                            payload_id = event['payload']['number']
                        if 'pull_request' in event['payload']:
                            payload_id = event['payload']['pull_request']['number']
                        if 'issue' in event['payload']:
                            payload_id = event['payload']['issue']['number']
                    if type == 'Push':
                        if 'commits' in event['payload']:
                            if len(event['payload']['commits']) > 0:
                                payload_id = event['payload']['commits'][0]['sha']
                    if type == 'Wiki':
                        if 'pages' in event['payload']:
                            payload_id = event['payload']['pages'][0]['sha']

                    action = None
                    if 'payload' in event:
                        if 'action' in event['payload']:
                            action = event['payload']['action'].title()
                    if type == 'Create':
                        action = 'Created {}'.format(event['payload']['ref_type'].title())
                    if type == 'Delete':
                        action = 'Deleted {}'.format(event['payload']['ref_type'].title())
                    if type == 'Wiki':
                        if 'pages' in event['payload']:
                            action = event['payload']['pages'][0]['action'].title()

                    url = None
                    if 'payload' in event:
                        if 'comment' in event['payload']:
                            url = event['payload']['comment']['html_url']
                        if 'pull_request' in event['payload']:
                            url = event['payload']['pull_request']['html_url']
                        if 'issue' in event['payload']:
                            url = event['payload']['issue']['html_url']
                    if type == 'Push':
                        if 'commits' in event['payload']:
                            if len(event['payload']['commits']) > 0:
                                url = event['payload']['commits'][0]['url'].replace('api.', '').replace('repos/', '')
                    if type == 'Wiki':
                        if 'pages' in event['payload']:
                            url = event['payload']['pages'][0]['html_url']

                    title = None
                    if 'payload' in event:
                        if 'pull_request' in event['payload']:
                            title = event['payload']['pull_request']['title']
                        if 'issue' in event['payload']:
                            title = event['payload']['issue']['title']
                    if type == 'Push':
                        if len(event['payload']['commits']) > 0:
                            title = '{}: {}'.format(event['payload']['ref'],
                                                    event['payload']['commits'][0]['message'].split('\n')[0])
                    if type == 'Create' or type == 'Delete':
                        title = event['payload']['ref']
                    if type == 'Wiki':
                        if 'pages' in event['payload']:
                            title = event['payload']['pages'][0]['title']

                    self.cur.execute('SELECT event_id FROM event WHERE source_id = ?', (event['id'],))
                    row = self.cur.fetchone()

                    if row == None:
                        self.cur.execute('INSERT INTO event(user_id, created_at, source, source_id, repo, event, '
                                         'payload_id, action, url, title) '
                                         'VALUES(?,?,?,?,?,?,?,?,?,?'
                                         ')', (user_id,
                                               event['created_at'],
                                               'GitHub',
                                               event['id'],
                                               repo['name'],
                                               type,
                                               payload_id,
                                               action,
                                               url,
                                               title))
                        self.conn.commit()
                    else:
                        self.cur.execute('UPDATE event SET '
                                         'user_id = ?, '
                                         'created_at = ?, '
                                         'source = ?, '
                                         'source_id = ?, '
                                         'repo = ?, '
                                         'event = ?, '
                                         'payload_id = ?, '
                                         'action = ?, '
                                         'url = ?, '
                                         'title = ? '
                                         'WHERE event_id = ?', (user_id,
                                                                event['created_at'],
                                                                'GitHub',
                                                                event['id'],
                                                                repo['name'],
                                                                type,
                                                                payload_id,
                                                                action,
                                                                url,
                                                                title,
                                                                row[0]))
                        self.conn.commit()

        return
