#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import getpass

import utils.cli.git_utils as git_utils
from utils import server_config
from utils.cli.output import out, yellow, bold
from utils.config import Config

__author__ = 'Kevin Dubois'
__version__ = '1.0.0'

"""gpull: run gpull_local.py on server(s)"""


class GitPull(object):

    def __init__(self):
        """instantiate default variables to be used in the class"""
        # dict of server aliases and properties
        config = Config()
        self.server_aliases = config.servers

        # list of group aliases, eg. test-all, test-lex, stg-cr
        self.group_aliases = server_config.get_group_aliases(self.server_aliases)

    def main(self):
        """Parse arguments and then call the appropriate function(s)."""

        parser = argparse.ArgumentParser(description="""Pull multiple Git Repositories at once, on multiple servers.""")

        parser.add_argument('-p', '--path', nargs="*", metavar="path", default=None,
                            help="""update all repositories under this directory / path (or the directory itself,
                            if the given directory corresponds to a repo. eg. -p ots /srv/salt )""")

        parser.add_argument('-b', '--branch', metavar="branch", nargs='?', default=None,
                            help="""check the repo out on the specified branch if it's not on this branch yet.""")

        parser.add_argument('-f', '--force', nargs='?', default=False, metavar="force pull/checkout",
                            help="""force checkout / pull (discard local changes) if we're changing branches.""")

        parser.add_argument('-a', '--all', nargs='?', default=False, metavar="recurse through all directories",
                            help="""Recurse through all subdirectories to find git repos.""")

        # get all aliases and sort them for help convenience
        all_aliases = sorted(
            list(self.server_aliases.keys()) +
            list(self.group_aliases.keys())
        )

        parser.add_argument('-s', '--servers', nargs="*", metavar="servers", default=None,
                            help="A list of server aliases to update. \n "
                                 "List of all available server aliases: {}".format(", ".join(all_aliases)))

        parser.add_argument('-u', '--remote-user', nargs='?', default=None, metavar="your ssh username",
                            help="""ssh into into git server with this user""")

        args = parser.parse_args()

        out(0, (yellow(bold("gpull") + ": remotely pull git repos")))

        if args.servers is not None:
            pw = getpass.getpass("Your ssh password:")  # Prompt user for ssh password
        else:
            pw = None  # No password needed to update your local folders

        gitutils = git_utils.GitUtils()
        gitutils.remote_pull(args.path, args.branch, args.force, args.servers, args.remote_user, pw, args.all)


if __name__ == "__main__":
    try:
        GitPull = GitPull()
        GitPull.main()
    except KeyboardInterrupt:
        out(0, "Stopped by user.")
