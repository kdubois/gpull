#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
import utils.cli.git_utils as gpull
from utils.cli.output import out, blue, yellow, green, bold, red

__author__ = 'Kevin Dubois'
__version__ = '0.0.1'


class GitMergeAll(object):
    def __init__(self):
        """instantiate default variables to be used in the class"""
        self.gitutils = gpull.GitUtils()

    def main(self):
        """Parse arguments and then call the appropriate function(s)."""

        parser = argparse.ArgumentParser(description="""Merge one branch (-b) to another (-t)""")

        parser.add_argument('-b', '--branch', nargs='?', metavar="branch", required=True,
                            help="""branch to merge from""")

        parser.add_argument('-t', '--to_branch', nargs='?', metavar="to_branch", required=True,
                            help="""branch to merge into""")

        parser.add_argument('-o', '--one-way', nargs='?', metavar="one_way", required=False, default="True",
                            help="""Merge branch one way, or both ways if False""")

        args = parser.parse_args()

        try:
            self.merge_branches(args.branch, args.to_branch, args.one_way)

        except Exception as e:
            out(0, red(e))

    def merge_branches(self, branch, to_branch, one_way=True):

        if one_way is False:
            # first  merge to branch into the working branch
            out(1, blue("Pulling from {} and merging into {}".format(to_branch, branch)))
            output = self.gitutils.git_merge_all(to_branch, branch)

            if output is False:
                raise Exception("Aborting!! Could not run shell command :(")

        # Merge the from branch into the destination branch
        out(1, blue("Pulling from {} and merging into {}".format(branch, to_branch)))
        output = self.gitutils.git_merge_all(branch, to_branch)

        if output is False:
            raise Exception("Aborting!! Could not run shell command :(")

        return True


if __name__ == "__main__":
    try:
        StagePusher = GitMergeAll()
        StagePusher.main()
    except KeyboardInterrupt:
        out(0, "Stopped by user.")
