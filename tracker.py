import os
import sys
import argparse
import traceback
from util.github import GitHub
from util.builder import Builder


def main():
    try:
        parser = argparse.ArgumentParser(description='Multiple Issue Tracker ' \
                                                     'by Milestone on GitHub')
        parser.add_argument('--file', '-f',
            help='Write markdown to local file.')
        parser.add_argument('--issue', '-i',
            required=True,
            help='Reference to GitHub issue to update. In the format ' \
                 'of {account}/{repository}/issues/{issue number}. (Required)')
        parser.add_argument('--milestone', '-m',
            required=True,
            help='Milestone to filter on in repos. (Required)')
        parser.add_argument('--organization', '-o',
            required=True,
            help='Organization to scan. (Required)')
        parser.add_argument('--password', '-p',
            required=True,
            help='Your GitHub password. (Required)')
        parser.add_argument('--timezone', '-t',
            required=True,
            help='Timezone from the Olson database. (https://en.wikipedia' \
                 '.org/wiki/List_of_tz_database_time_zones)')
        parser.add_argument('--username', '-u',
            required=True,
            help='Your GitHub username. (Required)')

        args = parser.parse_args()

        github = GitHub(args.username, args.password, args.timezone)
        build = Builder(args.milestone, args.organization)

        # Get our organization
        org = github.get_org(args.organization)

        # Get a list of repositories in the organization
        repos = github.get_repos(org)
        repos = sorted(repos, key=lambda k: k['name'])

        for repo in repos:
            # Get a list of milestones in the repository
            milestones = github.get_milestones(args.organization,
                repo['name'])

            for milestone in milestones:
                if milestone['title'] == args.milestone:
                    # Get a list of issues in this milestone
                    issues = github.get_issues(args.organization,
                        repo['name'],
                        milestone['number'])

                    if len(issues) > 0:
                        # Initialize our Builder
                        build.init(repo['name'], issues)

        markdown = build.get_markdown(args.username)

        # Update our tracking issue
        github.update_issue(markdown, '%s' % args.issue)

        # Write out the issue text to a file
        if args.file is not None:
            with open(args.file, 'w') as out:
                out.truncate()
                out.write(markdown)

    except Exception as err:
        print('\n')
        traceback.print_exc(file=sys.stdout)
        print('\n')
        return 2

if __name__ == "__main__":
    sys.exit(main())
