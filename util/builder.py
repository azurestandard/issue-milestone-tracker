import operator
from datetime import datetime
from util.github import GITHUB_DATE_FORMAT


class Builder:
    def __init__(self, milestone_filter, organization):
        self.milestone_filter = milestone_filter
        self.organization = organization

        self.issues = []
        self.assignee_counts = []
        self.label_counts = []
        self.repo_counts = []
        self.day_opened_counts = []
        self.day_closed_counts = []
        self.milestones = []

    def add_issues(self, repo_name, issues, milestone):
        self.milestones.append([repo_name, milestone])

        for issue in issues:
            issue_type = 'Issue'
            if 'pull_request' in issue:
                issue_type = 'Pull'

            assignee = 'unassigned'
            if issue['assignee'] is not None:
                assignee = issue['assignee']['login']

            labels = ''
            first = True
            if len(issue['labels']) > 0:
                for label in issue['labels']:
                    if first:
                        labels += '`{}`'.format(label['name'])
                        first = False
                    else:
                        labels += ', `{}`'.format(label['name'])

                    self.label_counts = self.add_counts(
                        self.label_counts,
                        label['name'].lower(),
                        issue)
            else:
                self.label_counts = self.add_counts(
                    self.label_counts,
                    'none',
                    issue)

            created_at = ''
            if issue['created_at'] is not None:
                created_at = datetime.strptime(
                    issue['created_at'],
                    '%Y-%m-%dT%H:%M:%SZ')
                self.day_opened_counts = self.add_counts(
                    self.day_opened_counts,
                    created_at.strftime('%Y-%m-%d'),
                    issue)

            closed_at = ''
            if issue['closed_at'] is not None:
                closed_at = datetime.strptime(
                    issue['closed_at'],
                    '%Y-%m-%dT%H:%M:%SZ')
                self.day_closed_counts = self.add_counts(
                    self.day_closed_counts,
                    closed_at.strftime('%Y-%m-%d'),
                    issue)

            state_order = 'a'
            if issue['state'] == 'closed':
                state_order = 'b'

            self.issues.append(('{}{}{}{}'.format(
                repo_name,
                state_order,
                issue['state'],
                assignee), {
                    'repo': repo_name,
                    'state': issue['state'],
                    'type': issue_type,
                    'number': issue['number'],
                    'url': issue['html_url'],
                    'title': issue['title'],
                    'labels': labels,
                    'assignee': assignee,
                    'created_at': created_at,
                    'closed_at': closed_at
                }
            ))

            self.assignee_counts = self.add_counts(
                self.assignee_counts,
                assignee.lower(),
                issue)

            self.repo_counts = self.add_counts(
                self.repo_counts,
                repo_name.lower(),
                issue)

    def add_counts(self, counts, label, issue):
        add_item = True
        for item in counts:
            if item['name'] == label:
                if issue['state'] == 'open':
                    if 'pull_request' not in issue:
                        item['counts']['issues_open'] += 1
                    else:
                        item['counts']['pulls_open'] += 1
                else:
                    if 'pull_request' not in issue:
                        item['counts']['issues_closed'] += 1
                    else:
                        item['counts']['pulls_closed'] += 1
                add_item = False
                break

        if add_item:
            issues_open = 0
            issues_closed = 0
            pulls_open = 0
            pulls_closed = 0

            if issue['state'] == 'open':
                if 'pull_request' not in issue:
                    issues_open = 1
                else:
                    pulls_open = 1
            else:
                if 'pull_request' not in issue:
                    issues_closed = 1
                else:
                    pulls_closed = 1

            value = {
                'name': label,
                'counts': {
                    'issues_open': issues_open,
                    'issues_closed': issues_closed,
                    'pulls_open': pulls_open,
                    'pulls_closed': pulls_closed
                }
            }
            counts.append(value)

        return counts

    def get_count_chart(self, counts, label, row_counts=True, col_counts=True):
        issues_open = 0
        issues_closed = 0
        pulls_open = 0
        pulls_closed = 0
        counts = sorted(counts, key=lambda k: k['name'])
        if row_counts:
            md = ('{} | Issues Opened | Issues Closed | Pulls Open |'
                  'Pulls Closed | Open Totals | Closed Totals | '
                  'Totals\n'.format(label))
            md += ':-- | --: | --: | --: | --: | --: | --: | --:\n'
        else:
            md = ('{} | Issues Opened | Issues Closed | Pulls Open |'
                  'Pulls Closed\n'.format(label))
            md += ':-- | --: | --: | --: | --:\n'
        for value in counts:
            if row_counts:
                issues_open += value['counts']['issues_open']
                issues_closed += value['counts']['issues_closed']
                pulls_open += value['counts']['pulls_open']
                pulls_closed += value['counts']['pulls_closed']

                total_open = value['counts']['issues_open'] + \
                    value['counts']['pulls_open']
                total_closed = value['counts']['issues_closed'] + \
                    value['counts']['pulls_closed']
                total_issues = total_open + total_closed
                percent_complete = 100
                if total_closed == 0:
                    percent_complete = 0
                elif total_open != 0:
                    percent_complete = int(
                        round((total_closed / total_issues) * 100))

                md += ('**{}** | {} | {} | {} | {} | **{}** | **{}** |'
                       '**{}** (*{}*%)\n'.format(
                           value['name'],
                           value['counts']['issues_open'],
                           value['counts']['issues_closed'],
                           value['counts']['pulls_open'],
                           value['counts']['pulls_closed'],
                           total_open,
                           total_closed,
                           total_issues,
                           percent_complete))
            else:
                md += '**{}** | {} | {} | {} | {}\n'.format(
                    value['name'],
                    value['counts']['issues_open'],
                    value['counts']['issues_closed'],
                    value['counts']['pulls_open'],
                    value['counts']['pulls_closed'])
        if col_counts:
            md += '**Totals** | **{}** | **{}** | **{}** | **{}** |\n'.format(
                issues_open,
                issues_closed,
                pulls_open,
                pulls_closed)

        return md

    def get_day_chart(self, counts_opened, counts_closed):
        counts_opened = sorted(
            counts_opened,
            key=lambda k: k['name'],
            reverse=True)
        counts_opened = counts_opened[:7]

        counts_closed = sorted(
            counts_closed,
            key=lambda k: k['name'],
            reverse=True)
        counts_closed = counts_closed[:7]

        counts = []
        for i in range(7):
            opened_day = None
            opened_total = None
            if len(counts_opened) > i:
                opened_day = counts_opened[i]['name']
                opened_total = (
                    counts_opened[i]['counts']['issues_open'] +
                    counts_opened[i]['counts']['pulls_open'])

            closed_day = ''
            closed_total = ''
            if len(counts_closed) > i:
                closed_day = counts_closed[i]['name']
                closed_total = (
                    counts_closed[i]['counts']['issues_closed'] +
                    counts_closed[i]['counts']['pulls_closed'])

            counts.append({
                'opened_day': opened_day,
                'opened_total': opened_total,
                'closed_day': closed_day,
                'closed_total': closed_total
            })

        md = ('Opened On | Total | <---------- Past 7 Work Day Totals'
              ' ----------> | Closed On | Total\n')
        md += ':-- | --: | :--: | :-- | --:\n'
        for value in counts:
            md += '**{}** | {} | | **{}** | {}\n'.format(
                value['opened_day'],
                value['opened_total'],
                value['closed_day'],
                value['closed_total'])

        return md

    def get_issue_detail_listing(self):
        issues = sorted(self.issues, key=operator.itemgetter(0))

        repo = ''
        state = ''
        assignee = ''
        md = ''

        for issue in issues:
            high = ''
            issue = issue[1]
            if repo != issue['repo']:
                repo = issue['repo']
                state = ''
                assignee = ''
                md += '\n### {}\n\n'.format(repo)

            if state != issue['state']:
                state = issue['state']
                assignee = ''
                if issue['state'] == 'open':
                    md += '- :pencil2: **{}**\n'.format(state)
                else:
                    md += '- :closed_book: **{}**\n'.format(state)

            if assignee != issue['assignee']:
                assignee = issue['assignee']
                md += '  - :bust_in_silhouette: **{}**\n'.format(assignee)

            box_state = '[ ]'
            strike = ''
            if issue['state'] == 'closed':
                box_state = '[X]'
                strike = '~~'

            date_string = ''
            if issue['closed_at'] != '':
                date_string = 'Closed: {}'.format(issue['closed_at'].strftime('%m-%d-%Y'))
            elif issue['created_at'] != '':
                date_string = 'Opened: {}'.format(issue['created_at'].strftime('%m-%d-%Y'))

            if 'High Priority' in issue['labels']:
                high = ':fire:'

            md += '    - {} {}{}{} [#{}]({}): {}{}{} - {}\n'.format(
                box_state,
                strike,
                high,
                issue['type'],
                issue['number'],
                issue['url'],
                issue['title'],
                issue['labels'],
                strike,
                date_string
                )

        if issue['state'] == 'open':
            return md
        else:
            return ''

    def get_milestone_totals(self):
        percent_complete = 100
        issues_open = 0
        issues_closed = 0

        for milestone in self.milestones:
            milestone = milestone[1]
            issues_open += int(milestone['open_issues'])
            issues_closed += int(milestone['closed_issues'])

        issues_total = issues_open + issues_closed
        if issues_closed == 0:
            percent_complete = 0
        elif issues_open != 0:
            percent_complete = int(round((issues_closed / issues_total) * 100))
        party = ''
        if percent_complete == 100:
            party = ' :tada:'

        md = ':checkered_flag: **Percentage Completed:** *{}*%{}\n'.format(
            percent_complete, party)
        md += ':pencil2: **Issues Opened:** *{}*\n'.format(
            issues_open)
        md += ':closed_book: **Issues Closed:** *{}*\n'.format(
            issues_closed)
        md += ':heavy_check_mark: **Issues Total:** *{}*\n\n'.format(
            issues_total)

        return md

    def get_milestone_detials(self):
        md = 'Repository | Details\n'
        md += ':-- | :--\n'
        for milestone in self.milestones:
            repo = milestone[0]
            milestone = milestone[1]
            due_on = None
            if milestone['due_on']:
                due_on = datetime.strptime(
                    milestone['due_on'],
                    GITHUB_DATE_FORMAT)
            description = 'N/A'
            if milestone['description']:
                description = milestone['description']
            md += ('**[{}]({})** | :page_facing_up: '
                   '**Description:** *{}*\n'.format(
                       repo, milestone['html_url'], description))
            open_issues = milestone['open_issues']
            closed_issues = milestone['closed_issues']
            percent_complete = 100
            if closed_issues == 0:
                percent_complete = 0
            elif open_issues != 0:
                total_issues = open_issues + closed_issues
                percent_complete = int(
                    round((closed_issues / total_issues) * 100))
            party = ''
            if percent_complete == 100:
                party = ' :tada:'

            md += (' | :checkered_flag: **Percentage Completed:** '
                   '*{}*%{}\n'.format(percent_complete, party))
            md += (' | :pencil2: **Opened:** *{}*\n'.format(
                milestone['open_issues']))
            md += (' | :closed_book: **Closed:** *{}*\n'.format(
                milestone['closed_issues']))
            days = 0
            if due_on:
                days = (due_on.date() - datetime.now().date()).days
            day_text = ''
            if days < 0:
                day_text = '{} days ago'.format(abs(days))
            elif days == 0:
                day_text = 'Today'
            elif days > 0:
                day_text = '{} days from now'.format(days)
            if due_on:
                md += ' | :calendar: **Due On:** *{}* ({})\n'.format(
                    due_on.strftime("%B %d, %Y"), day_text)
            else:
                md += ' | :calendar: **Due On:** *N/A*\n'
            md += ' | \n'

        return md

    def get_markdown(self, username):
        markdown = '# Overview\n\n'
        markdown += ('Tracking of `{}`\'s repositories for '
                     'milestone `{}`.\n\n'.format(
                         self.organization,
                         self.milestone_filter))
        markdown += '### Overall Stats\n\n'
        markdown += self.get_milestone_totals()
        markdown += '### Milstone Details by Repository:\n\n'
        markdown += self.get_milestone_detials()
        markdown += '\n# Aggregated Data\n\n'
        markdown += '## :chart: Repositories\n\n'
        markdown += self.get_count_chart(self.repo_counts, 'Repository')
        markdown += '\n## :chart: Assignees\n\n'
        markdown += self.get_count_chart(self.assignee_counts, 'Assignee')
        markdown += '\n## :chart: Labels\n\n'
        markdown += self.get_count_chart(self.label_counts,
                                         'Label',
                                         col_counts=False)
        markdown += '\n## :chart: Days\n\n'
        markdown += self.get_day_chart(self.day_opened_counts,
                                       self.day_closed_counts)
        markdown += '\n# Repository Details\n'
        markdown += self.get_issue_detail_listing()
        markdown += '\n# Notes\n\n'
        markdown += ('This issue is automatically updated by a [python script]'
                     '(https://github.com/azurestandard/issue-milestone-'
                     'tracker).  This script goes through all `{}` '
                     'repositories and lists issues under the `{}` '
                     'milestone.  There is no need to check off '
                     'individual issues. The script will is manually '
                     'run to update the issue list periodically. '
                     'This script will check off closed items.  '
                     'Comments on this issue will be preserved '
                     'between updates.\n\n'.format(
                         self.organization,
                         self.milestone_filter))
        markdown += (':calendar: **Last Updated:** *{}* **By:** *{}*.'
                     '**Via:** [issue-milestone-tracker]'
                     '(https://github.com/azurestandard/issue-'
                     'milestone-tracker)'.format(
                         datetime.now().strftime("%B %d, %Y at %r"),
                         username))

        return markdown
