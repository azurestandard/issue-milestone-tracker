import argparse
import sqlite3
import sys
import traceback

from util.database import Database, Event


def main():
    try:
        parser = argparse.ArgumentParser(description='Multiple Issue '
                                         'Tracker by Milestone on GitHub')
        parser.add_argument('--days', '-d',
                            required=True,
                            help='Days since last update.')
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

        conn = sqlite3.connect('events.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        cur = conn.cursor()

        db = Database(conn, cur)
        db.build()
        db.populate(args.organization, args.username, args.password, args.timezone)

        cur.execute("SELECT * "
                    "FROM data "
                    "WHERE created_at >= date('now', ? || ' days')", ((-int(args.days)), ))
        rows = cur.fetchall()

        created_date_new = None
        for row in rows:
            event = Event(row)
            if created_date_new != event.created_date:
                print('\n## {}\n'.format(event.created_date))

            source_id = ''
            if event.payload_id:
                source_id = '[{}]({})'.format(event.payload_id[:7], event.url)
            action = ''
            if event.action:
                action = '{}'.format(event.action)
            print('- **{}** {}\n'
                  '  - :wrench: {} {} {} (:memo:{})\n'
                  '  - :page_facing_up: {}'.format(event.created_time,
                                                   event.fullname,
                                                   action,
                                                   event.event,
                                                   source_id,
                                                   event.repo,
                                                   event.title))

            created_date_new = event.created_date

        cur.close()

    except:
        print('\n')
        traceback.print_exc(file=sys.stdout)
        print('\n')
        return 2

if __name__ == "__main__":
    sys.exit(main())
