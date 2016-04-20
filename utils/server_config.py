from utils.config import Config

__author__ = 'Kevin Dubois'


def get_group_aliases(servers=None):
    """
    Set up 'group aliases' so we can update multiple servers at once
    :param self:
    :param servers: dict
    :return: dict of group aliases
    """
    config = Config()
    if servers is None:
        servers = config.servers

    aliases = dict()

    for environment in config.environments:

        alias = environment + '-all'
        aliases[alias] = {
            'servers': [key for key, value in servers.items()
                        if value['env'] == environment]
        }

        for group in config.groups:

            alias = environment + '-' + group
            aliases[alias] = {
                'servers': [key for key, value in servers.items()
                            if value['env'] == environment and value['group'] == group]
            }

    return aliases
