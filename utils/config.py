import os
import yaml

CONFIG_FILE = 'settings.yaml'


class Config(object):

    def __init__(self):
        # get settings from settings.yaml
        config_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, CONFIG_FILE))
        with open(config_file_path, 'r') as yml:
            self.config = yaml.load(yml)

        self.groups = self.get_groups()
        self.environments = self.get_environments()
        self.servers = self.get_servers()
        self.email_settings = self.get_email_settings()
        self.default_dir = self.get_default_dir()
        self.repositories = self.get_repositories()

    def get_groups(self):
        if self.config['ServerGroups'] is None:
            groups = ['group1']
        elif not isinstance(self.config['ServerGroups'], list):
            raise AttributeError(
                'ServerGroups in config file must be of type list, {} given'.format(type(self.config['ServerGroups']))
            )
        else:
            groups = self.config["ServerGroups"]

        return groups

    def get_environments(self):
        if self.config['Environments'] is None:
            environments = ['default']
        elif not isinstance(self.config['Environments'], list):
            raise AttributeError(
                'Environments in config file must be of type list, {} given'.format(type(self.config['Environments']))
            )
        else:
            environments = self.config["Environments"]

        return environments

    def get_servers(self):
        if [self.config['Servers']] is None:
            raise Exception('No Server Aliases configured.  Please specify servers in your config file')
        elif not isinstance(self.config['Servers'], dict):
            raise AttributeError(
                'Servers in config file must be of type dict, {} given'.format(type(self.config['Servers']))
            )
        else:
            servers = self.config['Servers']

        # TODO: loop through list of servers and validate the individual dicts for correct structure

        return servers

    def get_email_settings(self):

        if self.config['EmailSettings'] is None:
            email_setttings = {
                'email_host': '',
                'email_from': '',
                'email_to': ''
            }
        elif not isinstance(self.config['EmailSettings'], dict):
            raise AttributeError(
                'Email Settings in config file must be of type dict, {} given'.format(type(self.config['EmailSettings']))
            )
        else:
            email_settings = self.config['EmailSettings']

        return email_settings

    def get_default_dir(self):

        if self.config['DefaultDir'] is None:
            return os.getcwd()
        else:
            return self.config['DefaultDir']

    def get_default_merge_dir(self):

        if self.config['MergeDir'] is None:
            raise AttributeError(
                'MergeDir must be set in settings.yml config file'
            )
        else:
            return self.config['MergeDir']

    def get_repositories(self):

        if [self.config['Repositories']] is None:
            repositories = []
        elif not isinstance(self.config['Repositories'], list):
            raise AttributeError(
                'Repositories in config file must be of type list, {} given'.format(type(self.config['Repositories']))
            )
        else:
            repositories = self.config['Repositories']

        return repositories

    def get_git_server(self):
        if self.config['GitServer'] is None:
            raise AttributeError(
                'GitServer must be set in settings.yml config file'
            )
        else:
            return self.config['GitServer']
