# Multiple Issue Tracker by Milestone on GitHub

This script will update a GitHub issue with statistics based on a milestone.  It builds these statistics from all repositories in a given organization.

Pull requests are welcome.

## Sample Usage

```
python3 tracker.py -u username -p password -o organization -i /{repository}/issues/{issue number} -m "My Milestone" -t "America/Los_Angeles"
```

## Parameters

Parameters | Description
---------- | -----------
-f, --file | Write markdown to local file.
-h, --help | Show Help
-i, --issue | Reference to GitHub issue to update. In the format of {account}/{repository}/issues/{issue number}. *(Required)*
-m, --milestone | Milestone to filter on in repos. *(Required)*
-o, --organization | Organization to scan. *(Required)*
-p, --password | Your GitHub password. *(Required)*
-t, --timezone | Timezone from the [Olson]((https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)) database.
-u, --username | Your GitHub username. *(Required)*
