from datetime import datetime

class Builder:
    def __init__(self, milestone_filter, organization):
        self.milestone_filter = milestone_filter
        self.organization = organization

        self.issue_list = ''
        self.assignee_counts = []
        self.label_counts = []
        self.repo_counts = []
        self.day_opened_counts = []
        self.day_closed_counts = []

    def init(self, repo_name, issues):
        self.issue_list += '\n## %s (Issues/Pulls: %s)\n\n' % (repo_name,
            len(issues))

        for issue in issues:
            issue_type = 'Issue'
            if 'pull_request' in issue:
                issue_type = 'Pull'

            assignee = 'unassigned'
            if issue['assignee'] is not None:
                assignee = issue['assignee']['login']

            state = '[ ]'
            strike = ''
            if issue['state'] == 'closed':
                state = '[X]'
                strike = '~~'

            labels = ''
            first = True
            if len(issue['labels']) > 0:
                for label in issue['labels']:
                    if first:
                        labels += '`%s`' % label['name']
                        first = False
                    else:
                        labels += ', `%s`' % label['name']

                    self.label_counts = self.add_counts(self.label_counts,
                        label['name'].lower(),
                        issue)
            else:
                self.label_counts = self.add_counts(self.label_counts,
                    'none',
                    issue)

            if issue['created_at'] is not None:
                created_at = datetime.strptime(issue['created_at'],
                    '%Y-%m-%dT%H:%M:%SZ')
                self.day_opened_counts = self.add_counts(self.day_opened_counts,
                    created_at.strftime('%Y-%m-%d'),
                    issue)

            if issue['closed_at'] is not None:
                closed_at = datetime.strptime(issue['closed_at'],
                    '%Y-%m-%dT%H:%M:%SZ')
                self.day_closed_counts = self.add_counts(self.day_closed_counts,
                    closed_at.strftime('%Y-%m-%d'),
                    issue)

            self.issue_list += '  - %s %s [#%s](%s): %s%s %s **(%s)**%s\n' % (
                state,
                issue_type,
                issue['number'],
                issue['html_url'],
                strike,
                issue['title'],
                labels,
                assignee,
                strike)

            self.assignee_counts = self.add_counts(self.assignee_counts,
                assignee.lower(),
                issue)

            self.repo_counts = self.add_counts(self.repo_counts,
                repo_name.lower(),
                issue)

    def get_issue_list(self):
        return self.issue_list

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

    def get_count_chart(self, counts, label):
        issues_open = 0
        issues_closed = 0
        pulls_open = 0
        pulls_closed = 0
        counts = sorted(counts,
            key=lambda k: k['name'])
        md = """%s | Issues Opened | Issues Closed | \
 Pulls Open | Pulls Closed | Open Totals | Closed Totals | Totals\n""" % label
        md += """:-- | --: | --: | --: | --: | --: | --: | --:\n"""
        for value in counts:
            issues_open += value['counts']['issues_open']
            issues_closed += value['counts']['issues_closed']
            pulls_open += value['counts']['pulls_open']
            pulls_closed += value['counts']['pulls_closed']

            md += '**%s** | %s | %s | %s | %s | **%s** | **%s** | **%s**\n' % (
                value['name'],
                value['counts']['issues_open'],
                value['counts']['issues_closed'],
                value['counts']['pulls_open'],
                value['counts']['pulls_closed'],
                (value['counts']['issues_open'] +
                    value['counts']['pulls_open']),
                (value['counts']['issues_closed'] +
                    value['counts']['pulls_closed']),
                (value['counts']['issues_open'] +
                    value['counts']['issues_closed'] +
                    value['counts']['pulls_open'] +
                    value['counts']['pulls_closed']))
        md += '**Totals** | **%s** | **%s** | **%s** | **%s** |\n' % (
            issues_open,
            issues_closed,
            pulls_open,
            pulls_closed)

        return md

    def get_day_chart(self, counts_opened, counts_closed):
        opened = 0
        counts_opened = sorted(counts_opened,
            key=lambda k: k['name'],
            reverse=True)
        counts_opened = counts_opened[:7]

        closed = 0
        counts_closed = sorted(counts_closed,
            key=lambda k: k['name'],
            reverse=True)
        counts_closed = counts_closed[:7]
        print(counts_closed)

        counts = []
        for i in range(7):
            opened_day = None
            opened_total = None
            if len(counts_opened) > i:
                opened_day = counts_opened[i]['name']
                opened_total = (counts_opened[i]['counts']['issues_open'] +
                    counts_opened[i]['counts']['pulls_open'])

            closed_day = ''
            closed_total = ''
            if len(counts_closed) > i:
                closed_day = counts_closed[i]['name']
                closed_total = (counts_closed[i]['counts']['issues_closed'] +
                    counts_closed[i]['counts']['pulls_closed'])

            counts.append({
                'opened_day': opened_day,
                'opened_total': opened_total,
                'closed_day': closed_day,
                'closed_total': closed_total
            })

        md = """Opened On | Total | <---------- Totals From Last 7 Days \
 ----------> | Closed On | Total\n"""
        md += """:-- | --: | :--: | :-- | --:\n"""
        for value in counts:
            md += '**%s** | %s | | **%s** | %s\n' % (
                value['opened_day'],
                value['opened_total'],
                value['closed_day'],
                value['closed_total'])

        return md

    def get_markdown(self, username):
        markdown = '# Overview\n\n'
        markdown += """This issue is automatically updated by a python script. \
This script goes through all `%s` repositories and lists issues \
under the `%s` milestone.  There is no need to check off individual issues. \
The script will is manually run to update the issue list periodically. \
This script will check off closed items.  Comments on this issue will be \
preserved between updates.\n\n""" % (self.organization, self.milestone_filter)
        markdown += '# Aggregated Data\n\n'
        markdown += '## Repositories\n\n'
        markdown += self.get_count_chart(self.repo_counts, 'Repository')
        markdown += '## Assignees\n\n'
        markdown += self.get_count_chart(self.assignee_counts, 'Assignee')
        markdown += '## Labels\n\n'
        markdown += self.get_count_chart(self.label_counts, 'Label')
        markdown += '## Days\n\n'
        markdown += self.get_day_chart(self.day_opened_counts,
            self.day_closed_counts)
        markdown += '# Repository Issues\n\n'
        markdown += self.issue_list
        markdown += '\n\n:calendar: **Last Updated:** *%s* **by** *%s*' % (
            datetime.now().strftime("%B %d, %Y  %r"),
            username)

        return markdown
