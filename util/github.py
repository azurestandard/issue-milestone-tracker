import json
import requests


class GitHub:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = 'https://api.github.com'

    def error_check(self, request):
        if request.status_code != 200:
            error = request.json()
            raise Exception('%s: %s (%s)' % (
                request.status_code,
                error['message'],
                error['documentation_url']))

        return request.json()

    def get_org(self, organization):
        url = '%s/orgs/%s' % (self.base_url, organization)
        headers = {'Accept': 'application/vnd.github.v3+json'}
        r = requests.get(url, headers=headers,
            auth=(self.username, self.password))

        return self.error_check(r)

    def get_repos(self, org):
        url = org['repos_url']
        params = {
            'sort': 'full_name',
            'page': '1',
            'per_page': '100'
        }
        headers = {'Accept': 'application/vnd.github.v3+json'}
        r = requests.get(url,
            params=params,
            headers=headers,
            auth=(self.username, self.password))

        return self.error_check(r)


    def get_milestones(self, org_name, repo_name):
        url = '%s/repos/%s/%s/milestones' % (self.base_url,
            org_name,
            repo_name)
        payload = {
            'state': 'open',
            'page': '1',
            'per_page': '100'
        }
        headers = {'Accept': 'application/vnd.github.v3+json'}
        r = requests.get(url,
            params=payload,
            headers=headers,
            auth=(self.username, self.password))

        return self.error_check(r)

    def get_issues(self, org_name, repo_name, milestone_number):
        # TODO: Need to add paging to issue api
        url = '%s/repos/%s/%s/issues' % (self.base_url,
            org_name,
            repo_name)
        payload = {
            'state': 'all',
            'milestone': milestone_number,
            'page': '1',
            'per_page': '100'
        }
        headers = {'Accept': 'application/vnd.github.v3+json'}
        r = requests.get(url,
            params=payload,
            headers=headers,
            auth=(self.username, self.password))

        return self.error_check(r)

    def update_issue(self, markdown, issue):
        url = '%s/repos/%s' % (self.base_url, issue)
        headers = {'Accept': 'application/vnd.github.v3+json'}
        data = {
            "body": markdown
        }
        r = requests.patch(url,
            data=json.dumps(data),
            headers=headers,
            auth=(self.username, self.password))

        return self.error_check(r)
