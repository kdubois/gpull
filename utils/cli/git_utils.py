import getpass
import os
import pipes
import shlex
import subprocess

import paramiko

from output import out, blue, yellow, green, red
from utils import server_config
from utils.config import Config
from .. import user_settings

__author__ = 'Kevin Dubois'


class GitUtils(object):
    """
    Utility class for Git helper commands
    """
    def __init__(self):
        """instantiate default variables to be used in the class
        :rtype : object
        """
        # logging.basicConfig()  // uncomment for debugging

        this_dir = os.path.dirname(os.path.abspath(__file__))

        # a list of directories that we want to run git commands in
        self.dir = []
        self.config = Config()
        # default directory, if none was passed in
        self.default_dir = self.config.default_dir
        self.git_server = self.config.get_git_server()

        self.gpull_local_location = os.path.join(this_dir, os.pardir, os.pardir, 'gpull_local.py')

        # whether to force pull/checkout or not
        self.force = False

        # what custom branch to pull/checkout
        self.branch = None

        # the username to use for ssh
        self.ssh_user = None

        # ssh password
        self.pw = None

        self.email_to = self.config.email_settings['email_to']

        # recurse through all directories if True, otherwise use git_repos_config instead
        self.all_dirs = False

        # dict of server aliases and properties
        self.server_aliases = self.config.servers

        # list of group aliases, eg. test-all, test-lex, stg-cr
        self.group_aliases = server_config.get_group_aliases(self.server_aliases)

        # dict of open ssh connections, so we can recycle the ones we already have open
        self.connections = {}

        # key to current ssh connection in the connections list
        self.current_conn_key = None

    def remote_pull(self, paths, branch, force, servers, remote_user, pw, all_dirs=False, remote_path=None):
        """
        Do a git pull on remote servers
        :param paths: list of paths to update
        :param branch: string of branch to pull
        :param force: bool if true, then do a force checkout (overwriting uncommitted changes)
        :param servers: list of servers to update
        :param remote_user: string of ssh user
        :param pw: string ssh password
        :param all_dirs:
        :param remote_path
        :return:
        """

        if remote_path is not None:
            self.gpull_local_location = remote_path

        if paths is not None:
            # loop through paths
            for path in paths:
                # if no slash exists, then append the given directory to the default path
                if '/' not in path:
                    self.dir.append("".join(self.default_dir) + '/' + path)
                # otherwise, just append the path to the list of directories
                else:
                    self.dir.append(path)
        else:
            # if no path was passed in, just use the default directory
            self.dir.append(self.default_dir)

        if force is True or force is None:
            self.force = True

        if all_dirs is True or all_dirs is None:
            self.all_dirs = True

        if branch is not None:
            self.branch = branch

        settings = user_settings.UserSettings()
        if remote_user is not None:
            settings.save_ssh_user(remote_user)
            self.ssh_user = remote_user
        else:
            # attempt to get user from db.
            self.ssh_user = settings.get_ssh_user()

        self.pw = pw

        self.update_servers(servers)

    def update_servers(self, servers):
        """
        loop through servers, and run commands on them.
        :param servers: list of servers
        :return: void
        """

        if servers is None:
            # run locally
            self.update_server(None, 'localhost')
        else:
            for srv in servers:
                # if the server is an actual server and not a group of servers:
                if srv in self.server_aliases:
                    for url in self.server_aliases[srv]['url']:
                        # grab configuration from the server aliases dictionary, and run the script on the server
                        self.update_server(
                            srv,
                            url)
                # if this is a server group alias
                elif srv in self.group_aliases:

                        # we need to run through each server individually
                        for srv_alias in self.group_aliases[srv]['servers']:
                            for url in self.server_aliases[srv_alias]['url']:
                                # legacy servers require direct ssh connection
                                self.update_server(
                                    srv_alias,
                                    url,
                                    self.server_aliases[srv_alias]['git_user'])

            # at the end of the loop, close all connection instances
            for connection in self.connections.values():
                connection.close()

    def update_server(self, ssh_alias=None, url=None, git_user='www-data'):
        """
        Update Individual Server
        :param ssh_alias:
        :param url:
        :param git_user:
        :return:
        """
        # run this file on the desired server.
        command = "python -u " + self.gpull_local_location

        if ssh_alias is not None:
            # start a remote connection to the server
            command += " -u {} -e {} -n '{}' ".format(git_user, self.email_to, self.ssh_user)
            if self.start_ssh(url) is False:
                # failed connection, so don't continue updating directories
                return False

        # add path:
        command += " -p {}".format(' '.join(self.dir))

        # run through optional commands (force, branch)
        if self.branch is not None:
            command += " -b {}".format(self.branch)

        if self.force:
            command += " -f "

        if self.all_dirs:
            command += " -a "

        out(0, green("running git updates on " + url))

        out(0, self.exec_shell(command))

    def git_merge_all(self, from_branch, to_branch, working_path='/var/release'):
        """
        Merge all Git Repositories from one branch into another.
        :param from_branch: What branch to merge from
        :param to_branch: What branch to merge into
        :param working_path:
        :return:
        """
        if not os.path.exists(working_path):
            # if path doesn't exist, create it:
            os.mkdir(working_path)

        os.chdir(working_path)

        for repo in self.config.repositories:
            os.chdir(working_path)
            out(1, blue("\n------- REPO: " + repo + " -------"))
            # see if the repo exists
            path = working_path+'/'+repo

            output = ''
            try:
                if not os.path.exists(path):
                    output += self.exec_shell('git clone '+self.git_server+'/'+repo+'.git ' + path)

                    if 'Access denied.' in output:
                        out(2, yellow('skipped'))
                        continue

                os.chdir(path)

                output += self.exec_shell('git reset --hard HEAD')
                output += self.exec_shell('git checkout --force {}'.format(from_branch))
                output += self.exec_shell('git pull')
                output += self.exec_shell('git checkout --force {}'.format(to_branch))
                output += self.exec_shell('git pull')
                output += self.exec_shell('git merge {}'.format(from_branch))
                output += self.exec_shell('git push origin {}'.format(to_branch))

                for line in output.splitlines(True):
                    if line.startswith('error') or line.startswith('CONFLICT'):
                        out(2, red(line))
                    else:
                        out(2, green(line))

            except Exception as e:
                out(2, red('Error: '))
                out(2, red(output))
                out(2, red(e))
                return False
        return output

    def start_ssh(self, url):
        """
        start an ssh connection
        :param url:
        :return:
        """
        # use current user if none was passed in.
        if self.ssh_user is None:
            self.ssh_user = getpass.getuser()

        # if we haven't already started this connection, start it
        if url not in self.connections:
            try:
                # paramiko.util.log_to_file("paramiko.log")
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.allow_agent = False
                ssh.connect(url, username=self.ssh_user, password=self.pw)

            except Exception as e:
                out(0, red("SSH connection to {} failed: ".format(url)))
                print(e)
                return False
            # add this connection to the list of open connections
            self.connections[url] = ssh

        # set ssh_alias as the current connection key to be used in exec_shell
        self.current_conn_key = url

        return True

    def exec_shell(self, command):
        """
        Execute a shell command and get the output.
        :param command: script command
        :return: string | False
        """
        if self.current_conn_key:
            ssh = self.connections[self.current_conn_key]
            encoded = pipes.quote(self.pw)
            sudo_cmd = "echo {pw} | sudo -S ".format(pw=encoded)

            stdin, stdout, stderr = ssh.exec_command(sudo_cmd + command, get_pty=True)
            out(0, stdout.read())

            if stderr:
                for line in stderr.readlines():
                    line = line.strip()
                    # ignore sudo password prompts
                    if '[sudo] password for' not in line:
                        out(0, line)
        else:
            try:
                # try to run the process, or return an error
                process = subprocess.Popen(shlex.split(command), bufsize=0,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                stdout, stderr = process.communicate()

                if stdout is not None:
                    return stdout
            except subprocess.CalledProcessError as e:
                print("Could not finish your request: " + e.output.decode('UTF-8'))
                return False

        return ''
