##############################################################################
#
# convenience utils/funcitons etc
#
##############################################################################

import random
import string
import sys
import ConfigParser
from os.path import expanduser, isfile

VERBOSE = True

if VERBOSE:
    def verbose_print(*args):
        """
        print each argument separately so caller doesn't need to
        stuff everything to be printed into a single string
        """
        for arg in args:
            print arg,
        print
else:
    def verbose_print(*args):
        pass


def get_file_data(fpath):
    """
    Function returns the content of given file in python string
    """
    try:
        config = open(fpath, "r")
        content = config.read()
        config.close()
        return content
    except EnvironmentError:
        print "Failed to read config from", fpath
        exit(1)


def get_random_string(length):
    """
    Function returns a random string of given length
    """
    return ''.join(random.choice(string.lowercase) for i in range(length))


def confirm_yes_no(question, default="yes"):
    """
    Function confirms user for yes or no for given question.

    Returns True for yes, False for no
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}

    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    # checking user input
    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def create_config(config_path):
    """
    I am called when ~/.openci does not exist. I ask the user for
    config values and write them to files
    """
    config = ConfigParser.RawConfigParser()
    config.add_section('git')

    git_server = raw_input(
        "git server[http://gitlab.com]:") or "http://gitlab.com"
    git_api_key = raw_input("git api key[prompt]:") or ''
    api_version = 1.0
    timeout = 10
    ci_server = raw_input(
        "ci server[http://127.0.0.1:8080]:") or "http://127.0.0.1:8080"
    ci_username = raw_input("ci user name[admin]:") or "admin"
    ci_password = raw_input("ci server[prompt]:") or ''

    config.set('git', 'server', git_server)
    config.set('git', 'api_key', git_api_key)
    config.set('git', 'version', api_version)
    config.set('git', 'timeout', timeout)
    config.add_section('ci')
    config.set('ci', 'server', ci_server)
    config.set('ci', 'user', ci_username)
    config.set('ci', 'password', ci_password)

    with open(expanduser('~/.openci'), 'wb') as configfile:
        config.write(configfile)


if __name__ == "__main__":
    # some quick tests for utils

    # check a confirmation from user
    confirm_yes_no("Do you want to delete ?")

    # check a random string list
    print [get_random_string(x) for x in range(20, 40)]
