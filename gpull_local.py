#!/usr/bin/env python2
# -*- coding: utf-8 -*-


import argparse
import os
import shlex
import subprocess

from utils.cli.output import out, blue, yellow, green, bold, red
from utils.config import Config

# Import smtplib for the actual sending function
import smtplib
import socket
# Import the email modules we'll need
from email.mime.text import MIMEText

__author__ = 'Kevin Dubois'
__version__ = '1.0.0'

"""
gpull: pull git repositories locally
"""


class GitPullLocal(object):

    def __init__(self):
        """
         set default server aliases and repos
        """
        self.config = Config()
        self.dir_list = [self.config.default_dir]
        self.force = False
        self.all_dirs = False
        self.branch = None
        self.git_user = None
        self.branch_changes = []
        self.email_host = self.config.email_settings['email_host']
        self.email_from = self.config.email_settings['email_from']

    def main(self):
        """Parse arguments and then call the appropriate function(s)."""
        parser = argparse.ArgumentParser(description="""Pull multiple Git Repositories at once.""")

        parser.add_argument('-p', '--path', nargs="*", metavar="path", default=None,
                            help="""update all repositories under this directory / path (or the directory itself,
                            if the given directory corresponds to a repo)""")

        parser.add_argument('-b', '--branch', metavar="checkout", nargs='?', default=None,
                            help="""check the repo out on the specified branch if it's not on this branch yet.""")

        parser.add_argument('-f', '--force', nargs='?', default=False, metavar="force pull/checkout",
                            help="""force checkout / pull (discard local changes) if we're changing branches.""")

        parser.add_argument('-a', '--all', nargs='?', default=False, metavar="recurse through all directories",
                            help="""Recurse through all subdirectories to find git repos.""")

        parser.add_argument('-u', '--user', nargs='?', default=None, metavar="user to do git commands as",
                            help="""remote system user to perform git commands as""")

        parser.add_argument('-e', '--email', nargs='?', default=None, metavar="email notification recipient",
                            help="""if an email is passed in, the script will
                            attempt to send an email if a branch got switched""")

        parser.add_argument('-n', '--name', nargs='?', default=None, metavar="Name of user running this script",
                            help="""This name will appear on the email that gets sent out if branches were changed""")

        args = parser.parse_args()

        if args.path is not None:
            self.dir_list = args.path

        self.force = True if args.force is None else args.force

        if args.all:
            self.all_dirs = args.all

        if args.branch is not None:
            self.branch = args.branch

        if args.user is not None:
            self.git_user = args.user

        self.update_directories()

        if args.email is not None:
            self.email_changes(args.email, args.name)

    def update_directories(self):
        """Update a list of directories supplied by command arguments."""
        for path in self.dir_list:
            path = os.path.abspath(path.replace('\\', '\\\\'))  # convert relative to absolute path
            path_name = os.path.split(path)[1]  # directory name; "x" in /path/to/x/
            self.update_directory(path, path_name)

    def update_directory(self, dir_path, dir_name):
        """First, make sure the specified object is actually a directory, then
        determine whether the directory is a git repo on its own or a directory
        of git repositories. If the former, update the single repository; if the
        latter, update all repositories contained within."""

        dir_long_name = "{} '{}'".format('directory', bold(dir_path))

        if not self.is_valid_directory(dir_path):
            out(0, red(dir_long_name + " is not a valid directory"))
            return False

        if self.directory_is_git_repo(dir_path):
            out(0, yellow(dir_long_name.capitalize()) + yellow(" is a git repository:"))
            self.update_repository(dir_path, dir_name)

        elif self.all_dirs is False:
            # get the repos from git_repos_config and loop through them.
            for repo_name in self.config.repositories:
                repo_path = os.path.join(dir_path, repo_name)
                if self.directory_is_git_repo(repo_path):
                    self.update_repository(repo_path, repo_name)

        else:
            repositories = []
            
            for item in os.listdir(dir_path):
                repo_path = os.path.join(dir_path, item)
                repo_name = os.path.join(dir_name, item)
                if self.directory_is_git_repo(repo_path):  # filter out non-repositories
                    repositories.append((repo_path, repo_name))

            num_of_repos = len(repositories)
            if num_of_repos == 1:
                out(0, yellow(dir_long_name.capitalize()) + yellow(" contains 1 git repository:"))
            else:
                out(0, yellow(dir_long_name.capitalize()) + yellow(" contains {} git repositories:".format(num_of_repos)))

            repositories.sort()  # go alphabetically instead of randomly
            for repo_path, repo_name in repositories:
                self.update_repository(repo_path, repo_name)

    def is_valid_directory(self, dir_path):
        try:
            os.listdir(dir_path)  # test if we can access this directory
            if not os.path.isdir(dir_path):
                return False
        except OSError:
            return False

        return True

    def directory_is_git_repo(self, directory_path):
        """
        Check if a directory is a git repository.
        :param directory_path:
        :return: bool
        """

        git_subfolder = os.path.join(directory_path, ".git")

        if self.is_valid_directory(git_subfolder):  # check for path/to/repository/.git
            return True

        return False

    def update_repository(self, repo_path, repo_name):
        """
        Update a single git repository by pulling from the remote.
        :param repo_path:
        :param repo_name:
        :return: bool
        """
        out(1, bold(repo_name) + ":")

        # cd into our folder so git commands target the correct repo
        os.chdir(repo_path)
        try:
            # what branch are we on?
            curr_branch = self.exec_shell("git rev-parse --abbrev-ref HEAD")
        except subprocess.CalledProcessError as e:
            curr_branch = False
            out(2, yellow("warning: ") + e.output.decode('UTF-8'))

        # strip out spaces, new lines etc
        if curr_branch:
            curr_branch = curr_branch.strip(' \t\b\n\r')

        try:
            # check if there is anything to pull, but don't do it yet
            dry_fetch = self.exec_shell("git fetch --dry-run")
        except subprocess.CalledProcessError as e:
            out(2, red("Error: ") + "cannot fetch; do you have a remote repository configured correctly?\n" + e.output.decode('UTF-8'))
            return

        # if a specific branch was passed in, then make sure that's what we're on.
        if self.branch and curr_branch:
            branch = self.branch

            # if we're not on the required branch, then check it out.
            if branch != curr_branch:
                out(2, yellow("branch to switch from: " + curr_branch + "\nbranch to switch to: " + branch))
                try:
                    # need to fetch first
                    git_fetch_txt = self.exec_shell("git fetch")
                    if git_fetch_txt:
                        out(2, yellow(git_fetch_txt.strip()))
                except subprocess.CalledProcessError as e:
                    out(2, red("Could not fetch: \n" + e.output.decode('UTF-8')))
                    return False

                # get list of remote branches
                remote_branches = self.exec_shell("git branch -a")

                # see if the desired branch exists remotely, otherwise skip this process.
                if "remotes/origin/"+branch in remote_branches:
                    out(2, green('Attempting to switch branch from ' + curr_branch + ' to ' + branch))
                    if self.force:
                        git_checkout_txt = self.exec_shell("git checkout -f " + branch)
                        out(2, yellow(git_checkout_txt))
                    else:
                        try:
                            git_checkout_txt = self.exec_shell("git checkout " + branch)
                            out(2, yellow(git_checkout_txt))
                        except subprocess.CalledProcessError as e:
                            out(2, red("Could not check out branch: \n" + e.output.decode('UTF-8')))
                            return False
                    self.branch_changes.append([repo_name, curr_branch, branch])
                    # set curr_branch to the branch we just changed to.
                    curr_branch = branch
                else:
                    out(2, red("branch {} does not exist. skipping checkout.".format(branch, repo_path)))

        try:
            last_commit = self.exec_shell("git log -n 1 --pretty=\"%ar\"")
            last_commit = last_commit.strip(' \t\b\n\r')
        except subprocess.CalledProcessError:
            last_commit = "never"  # couldn't get a log, so no commits

        if not dry_fetch:
            # try git status, just to make sure a fetch didn't happen without a pull:
            status = self.exec_shell("git status -uno")
            if "Your branch is behind" not in status:
                out(2, blue("No new changes.") + " Last commit was {}.".format(last_commit))
                return False

        # stuffs have happened!
        out(2, "There are new changes upstream...")
        status = self.exec_shell("git status")

        if not status.endswith("nothing to commit (working directory clean)"):
            out(2, red("Warning: ") + "you have uncommitted changes in this repository!")
            if self.force:
                out(2, red("Since force is enabled, I will now reset your branch:"))
                reset_result = self.exec_shell("git reset --hard HEAD")
                out(2, green(reset_result))

        out(2, green("Pulling changes..."))
        try:
            result = self.exec_shell("git pull")
        except subprocess.CalledProcessError as e:
            try:
                # if pull fails to pull because remote branch is not configured correctly:
                if 'You asked me to pull without telling me which branch' in e.output or \
                        'Please specify which branch you want to merge with' in e.output:
                    set_remote_branch = self.exec_shell(
                        "git branch --set-upstream-to {} origin/{}".format(curr_branch, curr_branch))
                    out(2, green(set_remote_branch))
                    result = self.exec_shell("git pull")
                elif self.force and 'Your local changes to the following files would be overwritten' in e.output:
                    reset_result = self.exec_shell("git reset --hard HEAD")
                    out(2, green(reset_result))
                    result = self.exec_shell("git pull")
                else:
                    out(2, red(e.output))
                    return False
            except subprocess.CalledProcessError as e:
                out(2, red(e.output))
                return False

        if result:
            if 'Already up-to-date' in result:
                out(2, "No new changes in your branch. However, upstream the following changes happened:")
            else:
                out(2, "The following changes were made {}:".format(last_commit))

            out(2, blue(result))

    def exec_shell(self, command):
        """Execute a shell command and get the output."""

        if self.git_user:
            # if git_user is set, then run the command as this user with sudo -u
            command = "sudo -u {user} {command}".format(user=self.git_user, command=command)
        # try to run the process, or return an error
        result = subprocess.check_output(shlex.split(command), stderr=subprocess.STDOUT)

        return result.decode('UTF-8')

    def email_changes(self, recipient, name):
        """
        Send an email if branches changed remotely
        :param recipient: string
        :param name: string
        :return: void
        """

        hostname = socket.gethostname()
        sender = self.email_from

        if name is None:
            name = "Someone"
        msg = name + " switched branches on " + hostname + ":"

        if self.branch_changes and len(self.branch_changes) > 0:

            for change in self.branch_changes:

                msg += "\n" + "-" * 60
                msg += "\n" + "Repository: "+change[0]
                msg += "\n" + "From: "+change[1]
                msg += "\n" + "To: "+change[2]
            msg += "\n" + "-" * 60
            # Create a text/plain message
            msg = MIMEText(msg)

            # me == the sender's email address
            # you == the recipient's email address
            msg['Subject'] = 'Repository branch change on ' + hostname
            msg['From'] = sender
            msg['To'] = recipient

            # Send the message via our own SMTP server, but don't include the
            # envelope header.
            try:
                s = smtplib.SMTP(self.email_host)
                s.sendmail(sender, [recipient], msg.as_string())
                s.quit()
            except Exception as e:
                print(e)
                out(0, red("Error sending email:\nMessage: "+str(e)+"\n")+bold("Email Content:\n")+msg.as_string())


if __name__ == "__main__":
    try:
        GitPull = GitPullLocal()
        GitPull.main()
    except KeyboardInterrupt:
        out(0, "Stopped by user.")
