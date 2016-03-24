import unittest
import sys
import ConfigParser
from mock import patch

from openci.ci import CI
from openci.jenkinsci import JenkinsCI
from openci.gitlabci import GitlabCI

from openci.utils import get_random_string
from openci.tests.mocked import *

import mocked


class CITestCase(unittest.TestCase):
    """
    Unit tests for CI interface/abstract class
    """
    def setUp(self):
        """
        Function sets up the params for test cases
        """
        config_path = 'openci/tests/openci.cfg'
        self.config = ConfigParser.ConfigParser()
        self.config.read(config_path)
        self.gitlab = GitlabCI(self.config.get('git', 'server'),
                               self.config.get('git', 'api_key'))

        with patch('jenkins.Jenkins') as mock:
            instance = mock.return_value
            instance.get_version.return_value = "Test Server Version 1.0"

            # patching functions
            instance.job_exists = mocked_job_exists
            instance.create_job = mocked_create_job
            instance.rename_job = mocked_rename_job
            instance.delete_job = mocked_delete_job
            instance.enable_job = mocked_enable_job
            instance.disable_job = mocked_disable_job
            instance.get_job_info = mocked_get_job_info

            # instantiating jenkins wrapper
            self.jenkinsci = JenkinsCI(
                    self.config.get('ci', 'server'),
                    self.config.get('ci', 'user'),
                    self.config.get('ci', 'password'))

        #################################
        # cli args for commands to test #
        #################################

        # args for jenkins list job
        self.list_job_args = ["openci", "list_jobs"]
        self.get_plugins_args = ["openci", "get_plugins"]
        self.create_job_args = ["openci", "create_job"]
        self.delete_job_args = ["openci", "delete_job"]

    @patch('jenkins.Jenkins')
    def test_ci_list_jobs(self, mock):
        """
        A quick test on getting jobs with openci CLI

        Test Plan:
        1. Overwrite sys args
        2. Call the openci CLI
        """
        # patching get_jobs()
        instance = mock.return_value
        instance.get_jobs = mocked_get_jobs

        # injecting args for jenkins list job
        sys.argv = self.list_job_args
        CI(self.config)

    @patch('jenkins.Jenkins')
    def test_get_plugins(self, mock):
        """
        A quick test on getting jenkins installed plugins with openci CLI

        1. Overwrite sys args
        2. Call the openci CLI
        """
        # patching get_plugins()
        instance = mock.return_value
        instance.get_plugins = mocked_get_plugins

        # injecting args for jenkins get plugins
        sys.argv = self.get_plugins_args
        CI(self.config)

    @patch('jenkins.Jenkins')
    def test_create_job(self, mock):
        """
        A quick test on creating a job on jenkins server with CLI args

        1. Overwrite sys args with args for jenkins create job
        2. Call the openci CLI
        """
        # patching create_job()
        instance = mock.return_value
        instance.create_job = mocked_create_job
        instance.job_exists = mocked_job_exists

        # adding a random job name to CLI args
        job_name = get_random_string(64)
        self.create_job_args.append(job_name)

        # injecting args for jenkins create job
        sys.argv = self.create_job_args
        CI(self.config)

        # assert that above created job exists on jenkins server
        self.assertTrue(self.jenkinsci.job_exists(job_name))

    @patch('jenkins.Jenkins')
    def test_create_job_with_config(self, mock):
        """
        A quick test on creating a job on jenkins server with CLI args,
        with a xml config file

        1. Overwrite sys args with args for jenkins create job
        2. Call the openci CLI
        """
        # patching create_job()
        instance = mock.return_value
        instance.create_job = mocked_create_job
        instance.job_exists = mocked_job_exists

        # adding a random job name to CLI args
        job_name = get_random_string(64)
        self.create_job_args.append(job_name)

        # adding xml config file
        self.create_job_args.append("--config")
        self.create_job_args.append("openci/config_samples/config.xml")

        # injecting args for jenkins create job
        sys.argv = self.create_job_args
        CI(self.config)

        # assert that above created job exists on jenkins server
        self.assertTrue(self.jenkinsci.job_exists(job_name))

    @patch('jenkins.Jenkins')
    def test_delete_job(self, mock):
        """
        A quick test to delete jenkins job with cli
        """
        # patching delete_job()
        instance = mock.return_value
        instance.delete_job = mocked_delete_job
        instance.create_job = mocked_create_job
        instance.job_exists = mocked_job_exists

        # adding a random job name to CLI args
        job_name = get_random_string(64)

        # creating test job
        self.jenkinsci.create_empty_job(job_name)

        self.delete_job_args.append(job_name)

        # injecting args for jenkins create job
        sys.argv = self.delete_job_args
        CI(self.config)

        # assert that above created job exists on jenkins server
        self.assertFalse(self.jenkinsci.job_exists(job_name))

    @patch('jenkins.Jenkins')
    def test_rename_job(self, mock):
        """
        CLI test case to rename a job
        """
        # patching rename_job()
        instance = mock.return_value
        instance.delete_job = mocked_delete_job
        instance.create_job = mocked_create_job
        instance.rename_job = mocked_rename_job
        instance.job_exists = mocked_job_exists

        from_name = get_random_string(128)
        to_name = get_random_string(128)

        self.jenkinsci.create_empty_job(from_name)

        # renaming job with CLI
        sys.argv = ["openci", "rename_job", from_name, to_name]
        CI(self.config)

        # asserting that job was renamed
        self.assertTrue(self.jenkinsci.job_exists(to_name))
        self.assertFalse(self.jenkinsci.job_exists(from_name))

    @patch('requests.post', side_effect=mocked.post_create_user)
    def test_curb_pass(self, mock):
        """
        CLI to test the curb command with params

        Test plan:-
         1. create random name, username, password, email & add them to args
         2. create random title, ssh key & add them to args
         3. create random repo and add them to args
         4. create random job, config and add them to args
         5. exec the CI
         6. assert that user exists
         7. assert that gitlab user exists
         8. assert that gitlab repo exists
         9. assert that jenkins job exist
        """
        # patching jenkins functions
        instance = mock.return_value
        instance.create_job = mocked_create_job
        instance.job_exists = mocked_job_exists

        curb_args = ["openci", "curb"]

        #######################################
        #                                     #
        # adding args for creating a new user #
        #                                     #
        #######################################
        name = get_random_string(16)
        username = get_random_string(32)
        password = get_random_string(8)
        email = "%s@%s.com" % (get_random_string(8), get_random_string(8))

        # adding args for new user
        curb_args.append(name)
        curb_args.append(username)
        curb_args.append(password)
        curb_args.append(email)

        ##################################
        #                                #
        # adding args for adding ssh key #
        #                                #
        ##################################
        title = "SSK key for %s" % name
        key = get_random_string(128)
        curb_args.append(title)
        curb_args.append(key)

        ###############################
        #                             #
        # adding args for gitlab repo #
        #                             #
        ###############################
        repo = get_random_string(32)
        curb_args.append(repo)

        ###############################
        #                             #
        # adding args for jenkins job #
        #                             #
        ###############################
        job = get_random_string(32)
        config = "openci/config_samples/config.xml"
        curb_args.append(job)
        curb_args.append(config)

        # executing curb command with args
        sys.argv = curb_args
        CI(self.config)

        ####################################
        #                                  #
        # asserting result of curb command #
        #                                  #
        ####################################
        self.assertTrue(username in self.gitlab.list_usernames())
        self.assertTrue(self.jenkinsci.job_exists(job))
