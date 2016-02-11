import json
import requests


class GitHub:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = 'https://api.github.com'
        self.per_page = 100

    def call(self, method, endpoint, params=None, data=None):
        headers = {'Accept': 'application/vnd.github.v3+json'}

        items = []
        while True:
            response = requests.request(method=method,
                auth=(self.username, self.password),
                headers=headers,
                url=endpoint,
                params=params,
                data=data)

            self.error_check(response)

            if type(response.json()) == dict:
                return response.json()

            items += response.json()

            if 'next' in response.links:
                endpoint = response.links['next']['url']
            else:
                break

        return items

    def error_check(self, response):
        if response.status_code != 200:
            error = response.json()
            raise Exception('Error %s: %s From: %s More Info: %s' % (
                response.status_code,
                error['message'],
                response.url,
                error['documentation_url']))

        return

    def get_org(self, organization):
        endpoint = '%s/orgs/%s' % (self.base_url, organization)
        return self.call('get', endpoint)

    def get_repos(self, org):
        endpoint = org['repos_url']
        params = {
            'sort': 'full_name',
            'per_page': self.per_page
        }
        return self.call('get', endpoint, params)

    def get_milestones(self, org_name, repo_name):
        endpoint = '%s/repos/%s/%s/milestones' % (self.base_url,
            org_name,
            repo_name)
        params = {
            'state': 'open',
            'per_page': self.per_page
        }
        return self.call('get', endpoint, params)

    def get_issues(self, org_name, repo_name, milestone_number):
        endpoint = '%s/repos/%s/%s/issues' % (self.base_url,
            org_name,
            repo_name)
        params = {
            'state': 'all',
            'milestone': milestone_number,
            'per_page': self.per_page
        }
        return self.call('get', endpoint, params)


    def update_issue(self, markdown, issue):
        endpoint = '%s/repos/%s' % (self.base_url, issue)
        headers = {'Accept': 'application/vnd.github.v3+json'}
        data = {
            "body": markdown
        }
        return self.call('patch', endpoint, data=json.dumps(data))
