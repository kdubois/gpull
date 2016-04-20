import sqlite3
import os

__author__ = 'Kevin Dubois'


class UserSettings(object):
    def __init__(self):
        this_dir = os.path.dirname(os.path.abspath(__file__))

        try:
            # create an sqlite connection to cache some user settings
            self.conn = sqlite3.connect(this_dir + '/user_settings.db')
            self.conn.row_factory = sqlite3.Row  # return select results as a dict instead of a tuple
            self.db = self.conn.cursor()

            # create user_settings table if it doesn't exist yet.
            self.create_table('user_settings')
        except:
            return False

    def save_ssh_user(self, user):
        """
        Cache ssh user in the user settings table
        :param user: string username
        :return: void
        """
        try:
            self.db.execute("INSERT OR REPLACE INTO user_settings (name, value) VALUES ('user', ?)", (user, ))
            self.conn.commit()
        except:
            return False

    def get_ssh_user(self):
        """
        Get cached ssh user
        :return: string / None
        """
        try:
            self.db.execute("SELECT value FROM user_settings WHERE name = 'user'")
            result = self.db.fetchone()

            if result:
                return result['value']
            else:
                return None
        except:
            return None

    def create_table(self, table):
        """
        Create a table if not exists
        :param table: table name
        :return: void
        """
        try:
            self.db.execute('''CREATE TABLE IF NOT EXISTS {}
                                (name TEXT UNIQUE NOT NULL, value TEXT NOT NULL)'''.format(table))
            self.conn.commit()
        except:
            return False