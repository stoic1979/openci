import unittest
import json
import ConfigParser
from mock import patch

from openci.gitlabci import GitlabCI
from openci.utils import get_random_string

from openci.tests import mocked


class GitlabCITestCase(unittest.TestCase):
    """
    Unit tests for GitlabCI interface/abstract class
    """

    def setUp(self):
        config_path = 'openci/tests/openci.cfg'
        self.config = ConfigParser.ConfigParser()
        self.config.read(config_path)
        self.gitlab = GitlabCI(self.config.get('git', 'server'),
                               self.config.get('git', 'api_key'))

        # dict with various params for a project
        self.proj_dict = {
                "name": get_random_string(64),
                "description": get_random_string(150),
                }

    @patch('requests.post', side_effect=mocked.post)
    def test_gitlab_create_project(self, mock_post):
        """
        test case to create a dummy project

        HTTP Response code should be 201

        FYI, HTTP 201 means:-
            The request has been fulfilled and
            resulted in a new resource being created
        """
        resp = self.gitlab.create_project({"name": get_random_string(54)})
        self.assertEqual(resp.status_code, 201)

    @patch('requests.post', side_effect=mocked.post)
    def test_gitlab_create_project_with_description(self, mock_post):
        """
        test case to create a dummy project

        HTTP Response code should be 201

        FYI, HTTP 201 means:-
            The request has been fulfilled and
            resulted in a new resource being created
        """
        resp = self.gitlab.create_project(self.proj_dict)
        self.assertEqual(resp.status_code, 201)

    @patch('requests.post', side_effect=mocked.post)
    def test_gitlab_create_project_with_details(self, mock_post):
        """
        test case to create a dummy project with name, description,
        issues enabled, wiki enabled, snippets enabled etc params
        """
        d = {
                "name": get_random_string(64),
                "description": get_random_string(256),
                "issues_enabled": "True",
                "wiki_enabled": "True",
                "snippets_enabled": "True",
                }
        resp = self.gitlab.create_project(d)
        self.assertEqual(resp.status_code, 201)

    @patch('requests.get', side_effect=mocked.get)
    def test_gitlab_list_all_projects(self, mock_get):
        """
        test case to list all projects
        """
        resp = self.gitlab.list_projects()
        self.assertEqual(resp.status_code, 200)

    @patch('requests.post', side_effect=mocked.post)
    def test_gitlab_fail_create_project_no_dict_params(self, mock_post):
        """
        asset to a dict type of params is passed to create project function
        """
        self.assertRaises(
                Exception, self.gitlab.create_project, "some-project-name")

    @patch('requests.post', side_effect=mocked.post)
    def test_gitlab_fail_create_project_dict_with_no_name_field(
            self, mock_post):
        """
        asset to get exception when cumpulsory field to create a project
        is not specified in params dict
        """
        self.assertRaises(
                Exception, self.gitlab.create_project,
                {"name1": "some-project-name"})

    @patch('requests.post', side_effect=mocked.post)
    def test_gitlab_create_user(self, mock_post):
        """
        Test plan:-
         1. create random name, username, password, email
         2. create user
         3. assert we get response 201 for user creation success
        """

        # step 1. create random name, username, password, email
        name = get_random_string(64)
        username = get_random_string(64)
        password = get_random_string(64)
        email = "%s@%s.com" % (get_random_string(16), get_random_string(16))

        # adding required arguments to create user in POST dict
        d = {
                "name": name,
                "username": username,
                "password": password,
                "email": email
                }

        print "creating user: %s", username

        # step 2. create user
        resp = self.gitlab.create_user(d)

        # 3. assert we get response 201
        self.assertTrue(resp.status_code == 201)
