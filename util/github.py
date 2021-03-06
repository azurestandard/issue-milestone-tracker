import json
import requests

from datetime import datetime, timedelta

GITHUB_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class GitHub:
    def __init__(self, username, password, timezone=None):
        self.username = username
        self.password = password
        self.timezone = timezone
        self.base_url = 'https://api.github.com'
        self.per_page = 100

    def call(self, method, endpoint, params=None, data=None):
        if self.timezone is None:
            headers = {
                'Accept': 'application/vnd.github.v3+json'
            }
        else:
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'Time-Zone': self.timezone
            }

        items = []
        while True:
            response = requests.request(method=method,
                                        auth=(self.username,
                                              self.password),
                                        headers=headers,
                                        url=endpoint,
                                        params=params,
                                        data=data)

            self.error_check(response)

            if type(response.json()) == dict:
                return response.json()
            else:
                items += response.json()

                if 'next' in response.links:
                    endpoint = response.links['next']['url']
                else:
                    break
        return items

    def error_check(self, response):
        if response.status_code != 200:
            error = response.json()
            raise Exception('Error {}: {} From: {} More Info: {}'.format(
                response.status_code,
                error['message'],
                response.url,
                error['documentation_url']))
        return

    def get_org(self, organization):
        endpoint = '{}/orgs/{}'.format(self.base_url, organization)
        return self.call('get', endpoint)

    def get_repos(self, org):
        endpoint = org['repos_url']
        params = {
            'sort': 'full_name',
            'per_page': self.per_page
        }
        return self.call('get', endpoint, params)

    def get_milestones(self, org_name, repo_name):
        endpoint = '{}/repos/{}/{}/milestones'.format(
            self.base_url,
            org_name,
            repo_name)
        params = {
            'state': 'open',
            'per_page': self.per_page
        }
        return self.call('get', endpoint, params)

    def get_issues(self, org_name, repo_name, milestone_number):
        endpoint = '{}/repos/{}/{}/issues'.format(
            self.base_url,
            org_name,
            repo_name)
        params = {
            'state': 'all',
            'milestone': milestone_number,
            'per_page': self.per_page
        }
        return self.call('get', endpoint, params)

    def get_closed_issues(self, org_name, repo_name, days):
        endpoint = '{}/repos/{}/{}/issues'.format(
            self.base_url,
            org_name,
            repo_name)

        since = datetime.now() - timedelta(days=int(days))
        since = since.strftime(GITHUB_DATE_FORMAT)

        params = {
            'state': 'closed',
            'since': since,
            'per_page': self.per_page
        }
        return self.call('get', endpoint, params)

    def update_issue(self, markdown, issue):
        endpoint = '{}/repos/{}'.format(self.base_url, issue)
        data = {
            "body": markdown
        }
        return self.call('patch', endpoint, data=json.dumps(data))

    def get_repo_events(self, org_name, repo_name):
        endpoint = '{}/repos/{}/{}/events'.format(
            self.base_url,
            org_name,
            repo_name)

        params = {
            'per_page': self.per_page
        }
        return self.call('get', endpoint)
