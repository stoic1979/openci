import unittest
import ConfigParser

from openci.jenkinsci import JenkinsCI
from openci.utils import get_random_string, get_file_data

from mock import patch

from openci.tests.mocked import *


class JenkinsCITestCase(unittest.TestCase):
    """
    Unit tests for JenkinsCI interface/abstract class
    """

    def setUp(self):
        config_path = 'openci/tests/openci.cfg'
        self.config = ConfigParser.ConfigParser()
        self.config.read(config_path)

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

    def _create_random_non_existing_job(self, length):
        while True:  # ugly loop !
            name = get_random_string(length)
            if not self.jenkinsci.job_exists(name):
                return name

    def test_get_server_version(self):
        """
        a quick test on jenkins server version
        """
        version = self.jenkinsci.get_version()
        print "Jenkins Server Version:", version
        self.assertIsNotNone(version)

    def test_create_empty_job(self):
        """
        test case to create an empty job on jenkins
        server with a random name
        """
        # get a random name for job
        job_name = get_random_string(64)
        self.jenkinsci.create_empty_job(job_name)

        # assert that above created job exists on jenkins server
        self.assertTrue(self.jenkinsci.job_exists(job_name))

        # assert that we can't create job with same name
        self.assertRaises(
                Exception, self.jenkinsci.create_empty_job, job_name)

    def test_create_job_with_config(self):
        """
        test case to create a job on jenkins with config xml
        server with a random name
        """
        # get a random name for job
        job_name = get_random_string(64)

        # creating jenkins job with a sample config file
        self.jenkinsci.create_job(
                job_name, get_file_data("openci/config_samples/config.xml"))

        # assert that above created job exists on jenkins server
        self.assertTrue(self.jenkinsci.job_exists(job_name))

        # assert that we can't create job with same name
        self.assertRaises(
                Exception, self.jenkinsci.create_empty_job, job_name)

        print "created job '%s' with config xml" % job_name

    def test_rename_job_pass(self):
        """
        Test plan:
        1. create a new project with random name
        2. create a new random name for the project
        3. ensure that jobs with names in 1. and 2. doesnt exist
        4. rename the job from 1. to 2.
        5. assert the changes
        6. cleanup test jobs
        """
        from_name = self._create_random_non_existing_job(16)
        to_name = self._create_random_non_existing_job(16)

        # we must create the job to be renamed
        self.jenkinsci.create_empty_job(from_name)

        # asserting that from_name job exists
        self.assertTrue(self.jenkinsci.job_exists(from_name))

        # renaming job
        self.jenkinsci.rename_job(from_name, to_name)
        print "renamed job from '%s' to '%s'" % (from_name, to_name)

        # asserting that job was renamed
        self.assertTrue(self.jenkinsci.job_exists(to_name))
        self.assertFalse(self.jenkinsci.job_exists(from_name))

        # we must create delete job that was renamed
        self.jenkinsci.delete_job(to_name)

        # asserting that job doesn't exist
        self.assertFalse(self.jenkinsci.job_exists(to_name))

    def test_rename_job_pass1(self):
        """
        quick fail test to check job rename failure for jobs
        with same names
        """
        to_name = from_name = self._create_random_non_existing_job(16)
        self.assertRaises(
                Exception, self.jenkinsci.rename_job, from_name, to_name)

    def test_enable_disable_job(self):
        """
        mixed test case to enable/disable jenkins job
        """
        job_name = self._create_random_non_existing_job(64)

        # we must create the job to be enabled
        self.jenkinsci.create_empty_job(job_name)

        # asserting that from_name job exists
        self.assertTrue(self.jenkinsci.job_exists(job_name))

        # disabling test job before enabling
        self.jenkinsci.disable_job(job_name)

        # asserting that job was disabled
        self.assertTrue(self.jenkinsci.is_job_disabled(job_name))

        # enabling test job before enabling
        self.jenkinsci.enable_job(job_name)

        # FIXME later !!!!
        self.assertFalse(self.jenkinsci.is_job_disabled(job_name))
