import sys
import argparse
import traceback
from util.github import GitHub
from util.builder import Builder


def main():
    try:
        parser = argparse.ArgumentParser(description='Multiple Issue '
                                         'Tracker by Milestone on GitHub')
        parser.add_argument('--days', '-d',
                            required=True,
                            help='Days since last update.')
        parser.add_argument('--file', '-f',
                            required=True,
                            help='Write markdown to local file.')
        parser.add_argument('--organization', '-o',
                            required=True,
                            help='Organization to scan. (Required)')
        parser.add_argument('--password', '-p',
                            required=True,
                            help='Your GitHub password. (Required)')
        parser.add_argument('--timezone', '-t',
                            help='Timezone from the Olson database. '
                            '(https://en.wikipedia.org/wiki/List_of_'
                            'tz_database_time_zones)')
        parser.add_argument('--username', '-u',
                            required=True,
                            help='Your GitHub username. (Required)')

        args = parser.parse_args()

        github = GitHub(args.username, args.password, args.timezone)

        # Get our organization
        org = github.get_org(args.organization)

        # Get a list of repositories in the organization
        repos = github.get_repos(org)
        repos = sorted(repos, key=lambda k: k['name'])

        for repo in repos:
            # Get a list of issues in this milestone
            issues = github.get_closed_issues(args.organization,
                                       repo['name'], args.days)

            if len(issues) > 0:
                print('\n### {}\n'.format(repo['name']))
                for issue in issues:
                    print('- [#{}](https://github.com/azurestandard/{}/issues/{}) - {} {}'.format(
                        issue['number'],
                        repo['name'],
                        issue['number'],
                        issue['title'],
                        issue['closed_at']
                    ))


        # Write out the closed items to a file
        #if args.file is not None:
        #    with open(args.file, 'w') as out:
        #        out.truncate()
        #        out.write(markdown)

    except:
        print('\n')
        traceback.print_exc(file=sys.stdout)
        print('\n')
        return 2

if __name__ == "__main__":
    sys.exit(main())
