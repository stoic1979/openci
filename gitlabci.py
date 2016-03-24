#!/usr/bin/python
from .utils import verbose_print

import requests
import json


class GitlabCI:
    """
    Class for performing various operations with gitlab
    like create project using Gitlab API.

    Gitlab API docs can be referred at:-
    http://doc.gitlab.com/ce/api/README.html
    """

    PROJECTS_SUFFIX = "/api/v3/projects"
    USERS_SUFFIX = "/api/v3/users"
    KEYS_SUFFIX = "/api/v3/user/keys"
    EMAILS_SUFFIX = "/api/v3/user/emails"

    def __init__(self, url, private_token):
        self.url = url
        self.projects_url = "%s%s" % (url, self.PROJECTS_SUFFIX)
        self.users_url = "%s%s" % (url, self.USERS_SUFFIX)
        self.keys_url = "%s%s" % (url, self.KEYS_SUFFIX)
        self.emails_url = "%s%s" % (url, self.EMAILS_SUFFIX)
        self.headers = {'PRIVATE-TOKEN': private_token}

    def create_project(self, params_dict):
        """
        Function creates a new project with specified parameters

        params_dict is a dict containing properties of project like name,
        description, issues_enabled, public, wiki_enabled etc
        """

        # assert that params_dict is a dict
        assert(isinstance(params_dict, dict))

        # assert that params_dict contains the value for cumpulsory field name
        # name field is used for assigning name to the project to be created
        assert('name' in params_dict)

        resp = requests.post(
                self.projects_url, data=params_dict, headers=self.headers)
        verbose_print(resp.content)

        return resp

    def remove_project(self, proj_id):
        """
        Function removes a project from gitlab server with given project id
        """
        url = "%s/%d" % (self.projects_url, int(proj_id))
        return requests.delete(url, headers=self.headers)

    def create_user(self, params_dict):
        """
        Function creates a new user on gitlab server,

        ** This operation needs admin rights for this **

        username, password and email must be specicifed in params_dict
        """

        # assert that params_dict is a dict
        assert(isinstance(params_dict, dict))

        # assert that params_dict contains the value for cumpulsory fields:-
        # name, password and email.
        assert('name' in params_dict)
        assert('username' in params_dict)
        assert('password' in params_dict)
        assert('email' in params_dict)

        resp = requests.post(
                self.users_url, data=params_dict, headers=self.headers)
        verbose_print("Server response: %s" % resp.content)
        verbose_print("Response code: %s" % resp.status_code)

        return resp

    def current_user(self):
        """
        Function gets information for currently authenticated user
        """
        url = "%s/api/v3/user" % self.url
        return requests.get(url, headers=self.headers)

    def delete_user(self, uid):
        """
        Functon deletes a user from gitlab server with given user id
        """
        url = "%s/%d" % (self.users_url, int(uid))
        return requests.delete(url, headers=self.headers)

    def list_users(self):
        """
        Function get list of all the gitlab user.

        ** This operation needs admin rights for this **
        """
        return requests.get(self.users_url, headers=self.headers)

    def list_usernames(self):
        """
        Function get list of all the gitlab usernames.

        ** This operation needs admin rights for this **
        """
        resp = requests.get(self.users_url, headers=self.headers)
        verbose_print(resp.content)
        if resp.status_code == 200:
            return [u["username"] for u in json.loads(resp.content)]
        return []

    def list_projects(self):
        """
        Function get list of all the projects
        """
        resp = requests.get(self.projects_url, headers=self.headers)
        verbose_print(resp.content)
        return resp

    def list_ssh_keys_for_user(self, id):
        """
        Function lists ssh keys for given user id

        ** This operation needs admin rights for this **
        """
        url = "%s/%d/keys" % (self.users_url, int(id))
        return requests.get(url, headers=self.headers)

    def add_ssh_key(self, title, key):
        """
        Function adds SSH key to gitlab user account

        Needs a title for the SSH key and the SSH key
        """
        # composing params dict for POST
        data = {"title": title, "key": key}

        resp = requests.post(self.keys_url, data=data, headers=self.headers)
        verbose_print(resp.content)
        return resp

    def add_ssh_key_user(self, id, title, key):
        """
        Function adds SSH key to gitlab user account

        Needs a user id, title for the SSH key and the SSH key

        ** This operation needs admin rights for this **
        """
        # composing params dict for POST
        data = {"id": id, "title": title, "key": key}

        # composing url for adding key for given user id
        url = "%s/api/v3/users/%d/keys" % (self.url, int(id))

        resp = requests.post(url, data=data, headers=self.headers)
        verbose_print(resp.content)
        return resp

    def remove_ssh_key(self, id):
        """
        Function remove a SSH key for an authenticated user with given id
        """
        url = "%s/%d" % (self.keys_url, int(id))
        return requests.delete(url, headers=self.headers)

    def remove_ssh_key_for_user(self, uid, kid):
        """
        Function remove a SSH key for an given user id and with given key id

        ** This operation needs admin rights for this **
        """
        url = "%s/%d/keys/%d" % (self.users_url, int(uid), int(kid))
        return requests.delete(url, headers=self.headers)

    def list_ssh_keys(self):
        """
        Function list SSH keys of an authenticated user on gitlab server
        """
        return requests.get(self.keys_url, headers=self.headers)

    def create_project_for_user(self, id, proj_name):
        """
        Function creates a new project owned by the specified user.

        ** This operation needs admin rights for this **
        """
        url = "%s/user/%d" % (self.projects_url, int(id))

        # composing params dict for POST
        data = {"user_id": id, "name": proj_name}

        return requests.post(url, data=data, headers=self.headers)

    def add_email(self, email):
        """
        Function adds given email to given user id
        """
        url = "%s/api/v3/user/emails" % self.url

        # composing params dict for POST
        data = {"email": email}
        return requests.post(url, data=data, headers=self.headers)

    def add_email_for_user(self, id, email):
        """
        Function adds given email to given user id

        ** This operation needs admin rights for this **
        """
        url = "%s/api/v3/users/%d/emails" % (self.url, int(id))

        # composing params dict for POST
        data = {"id": id, "email": email}

        return requests.post(url, data=data, headers=self.headers)

    def list_emails(self):
        """
        Function lists emails for current authenticated user
        """
        return requests.get(self.emails_url, headers=self.headers)

    def list_emails_for_user(self, id):
        """
        Function lists emails for current authenticated user
        """
        url = "%s/api/v3/users/%d/emails" % (self.url, int(id))
        return requests.get(url, headers=self.headers)
