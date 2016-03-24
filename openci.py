#!/usr/bin/python

import argparse
import sys
import json
import yaml
from os.path import expanduser, isfile
import ConfigParser

from .jenkinsci import JenkinsCI
from .gitlabci import GitlabCI

from utils import get_file_data, confirm_yes_no, create_config


class OpenCI(object):
    """
    command line script for OpenCI
    this will be the window to public

    Currently working with gitlab repos and Jenkins CI
    """
    def __init__(self, config=None):

        config_path = '~/.openci'
        self.config = ConfigParser.ConfigParser()
        
        # if we didn't pass in a config object but theres
        # a openci.conf in our current directory, use that
        if not config and isfile('openci.conf'):
            config = self.config.read('openci.conf')

        # If theres no config object passed in and no config
        # in our current directory try to load one from users home
        elif not config and not isfile('openci.conf'):

            if not isfile(expanduser(config_path)):
                create_config(config_path)

            self.config.read(expanduser(config_path))
        else:
            self.config = config

        # gitlab ci wrapper
        self.gitlabci = GitlabCI(self.config.get('git', 'server'),
                                 self.config.get('git', 'api_key'))

        # jenkins ci wrapper
        self.jenkinsci = JenkinsCI(self.config.get('ci', 'server'),
                                   self.config.get('ci', 'user'),
                                   self.config.get('ci', 'password'))

        # cli args parser
        parser = argparse.ArgumentParser(
            description='OpenCI commandline for continuous integration',
            usage='''ci <command> [<args>]

The most commonly used ci commands are:
   curb               Combo command to create a gitlab user, add ssh key
                      create specified project,
                      and create a jenkins job and triggers the build

   create_user        Create a new user on gitlab server
   current_user       Get information about current authenticated user
   delete_user        Delete a user from gitlab server
   list_users         Get list of all users on gitlab server
   list_usernames     Get list of all usernames on gitlab server
   create_project     Create a new project on gitlab server

   create_project_for_user
                      Create a new project on gitlab server for given user

   remove_project     Remove a project from gitlab server

   add_ssh_key        Add SSH key to gitlab user account
   add_ssh_key_user   Add SSH key to given gitlab's user account,
                      This command is available only for admin

   remove_ssh_key     Remove a SSH key from gitlab user account

   remove_ssh_key_for_user
                      Remove SSH key from gitlab's user account from
                      given user id and given key id
                      This command is available only for admin

   add_email          Adds given for user id

   add_email_for_user
                      Adds given for user id and email
                      This command is available only for admin

   list_emails        List emails for current user

   list_emails_for_user
                      List emails for given user id
                      This command is available only for admin

   list_ssh_keys      List SSH keys for given uid on gitlab server

   list_ssh_keys_for_user
                      List SSH keys for given uid on gitlab server
                      This command is available only for admin

   list_projects      Get list of all projects on gitlab server

   create_job         Create a new job on jenkins server
   create_view        Create a new view on jenkins server
   delete_view        Delete a view from jenkins server
   get_job_info       Get detailed information about the job
   debug_job_info     Get debug info for a jenkins job
   get_queue_info     Get a queue of jobs to be done
   list_jobs          Get list of all jobs on jenkins server
   get_jobs_names     Get names of all jobs on jenkins server
   jobs_count         Gets count of jons on jenkins server
   enable_job         Enable a job on jenkins server
   disable_job        Disable a job on jenkins server
   build_job          Build a job on jenkins server
   rename_job         Rename a job on jenkins server
   last_build_info    Get info for last build of a job on jenkins server
   delete_job         Delete a job on jenkins server
   get_plugins        Get info about all installed plugins on jenkins server
   get_plugin_info    Get info about of a jenkins plugins with given name
   get_plugin_names   Get names of all installed plugins on jenkins server
   jenkins_version    Get version of jenkins server
''')
        parser.add_argument('command', help='Subcommand to run')

        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print "Unrecognized command"
            parser.print_help()
            exit(1)

        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def jenkins_version(self):
        print "Jenkins:", self.jenkinsci.get_version()

    def list_projects(self):
        """
        Function returns a list of all project on gitlab server
        """
        resp = self.gitlabci.list_projects()
        data = json.loads(resp.content)
        print yaml.safe_dump(data)

    def curb(self):
        """
        Function parses/process command line args and runs the combo command.

        curb command creates a gitlab user with given name, add ssh key,
        then creates a specified project, a jenkins job and trigers its build
        """

        parser = argparse.ArgumentParser(
            description='Create a new user on gitlab server')

        # required fields for creating a gitlab user
        parser.add_argument('name', help='name of the user')
        parser.add_argument('username', help='username of the user')
        parser.add_argument('password', help='password of the user')
        parser.add_argument('email', help='email of the user')

        # required args for adding ssh keys
        parser.add_argument('title', help='title for SSH key')
        parser.add_argument('key', help='a valid ssh key')

        # gitlab repository name
        parser.add_argument('repo', help='name of the repository')

        # jenkins job name and config
        parser.add_argument('job', help='name of the jenkins job')
        parser.add_argument('config', help='config xml file')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        ##############################
        #                            #
        #    CREATING GITLAB USER    #
        #                            #
        ##############################

        # ensure password is atleast 8 chars
        if len(args.password) < 8:
            print "Password must be atleast 8 chars"
            return

        # adding required params to create a user
        params = {
                "name": args.name,
                "username": args.username,
                "password": args.password,
                "email": args.email
                }

        # no need for email confirmation for this new user
        params["confirm"] = "false"

        # creating new user on gitlab server
        resp = self.gitlabci.create_user(params)
        uid = 0
        if resp.status_code == 201:
            print "User '%s' created" % args.username
            rdata = json.loads(resp.content)
            uid = rdata["id"]
        else:
            data = json.loads(resp.content)
            print data["message"]
            return  # no need to continue, without creating user !!!

        ##############################
        #                            #
        #    ADDING SSH KEYS         #
        #                            #
        ##############################

        resp = self.gitlabci.add_ssh_key_user(uid, args.title, args.key)

        ##############################
        #                            #
        #    CREATING GITLAB REPO    #
        #                            #
        ##############################

        # creating repo/project with params
        resp = self.gitlabci.create_project_for_user(uid, args.repo)
        if resp.status_code == 201:
            print "Project '%s' created" % args.repo
        else:
            print "Failed to create '%s' project" % args.repo
            print "Server Response: %s" % resp.content
            return  # no need to continue, without creating repo !!!

        ##############################
        #                            #
        #    CREATING JENKINS JOB    #
        #                            #
        ##############################

        job = args.job

        # ensure that job doesnt exist
        if self.jenkinsci.job_exists(job):
            print "Error, Job '%s' already exist" % job
            return

        self.jenkinsci.create_job(job, get_file_data(args.config))
        print "Job '%s' created successfully" % job

        ##############################
        #                            #
        #    BUILDING JENKINS JOB    #
        #                            #
        ##############################

        # before building job, ensure it exists
        if not self.jenkinsci.job_exists(job):
            print "Error, Can't build job"
            print "Job '%s' doesn't exist" % job
            return  # no need to continue, without a job !!!

        # building job on jenkins server
        self.jenkinsci.build_job(job)
        print "Build trigered for job '%s'" % job

    def create_user(self):
        """
        Function parses/process command line args,
        and creates a new user on gitlab server

        This command needs admin permissions
        """
        parser = argparse.ArgumentParser(
            description='Create a new user on gitlab server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the user')
        parser.add_argument('username', help='username of the user')
        parser.add_argument('password', help='password of the user')
        parser.add_argument('email', help='email of the user')

        # optional arguments for user creation
        parser.add_argument('--skype', help='Skype ID')
        parser.add_argument('--linkedin', help='LinkedIn')
        parser.add_argument('--twitter', help='Twitter account')
        parser.add_argument('--website_url', help='Website URL')
        parser.add_argument(
                '--projects_limit', help='Number of projects user can create')
        parser.add_argument('--extern_uid', help='External UID')
        parser.add_argument('--provider', help='External provider name')
        parser.add_argument('--bio', help='User\'s biography')
        parser.add_argument(
                '--admin', help='User is admin - true or false (default)')
        parser.add_argument(
                '--can_create_group',
                help='User can create groups - true or false')
        parser.add_argument('--confirm', help='Require confirmation')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # ensure password is atleast 8 chars
        if len(args.password) < 8:
            print "Password must be atleast 8 chars"
            return

        # adding required arguments
        params = {
                "name": args.name,
                "username": args.username,
                "password": args.password,
                "email": args.email
                }

        # adding optional arguments
        if args.skype:
            params["skype"] = args.skype
        if args.linkedin:
            params["linkedin"] = args.linkedin
        if args.twitter:
            params["twitter"] = args.twitter
        if args.website_url:
            params["website_url"] = args.website_url
        if args.projects_limit:
            params["projects_limit"] = args.projects_limit
        if args.extern_uid:
            params["extern_uid"] = args.extern_uid
        if args.provider:
            params["provider"] = args.provider
        if args.bio:
            params["bio"] = args.bio
        if args.admin:
            params["admin"] = args.admin
        if args.can_create_group:
            params["can_create_group"] = args.can_create_group
        if args.confirm:
            params["confirm"] = args.confirm

        # creating new user on gitlab server
        resp = self.gitlabci.create_user(params)
        if resp.status_code == 201:
            print "User '%s' created" % args.username
        else:
            data = json.loads(resp.content)
            print data["message"]

    def current_user(self):
        """
        Function gets information about current authenticated user
        """
        resp = self.gitlabci.current_user()
        print resp.content

    def delete_user(self):
        """
        Function parses/process command line args,
        and deletes a user on gitlab server
        """
        parser = argparse.ArgumentParser(
            description='Delete a user from gitlab server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('id', help='id of the user')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # deleting a user from gitlab server
        resp = self.gitlabci.delete_user(args.id)

        if resp.status_code == 200:
            rdata = json.loads(resp.content)

            # null content in response implies that user does't exist
            if not rdata:
                print "Failed to remove user, user doen't exist"
                return

            # double checking that user was deleted from gitlab server
            if rdata["id"] == int(args.id):
                print "User deleted successfully"
        else:
            print "Failed to delete user from gitlab server"
            print "Server Response: %s" % resp.content

    def list_users(self):
        """
        Function parses/process command line args,
        and lists all the users on gitlab server
        """
        resp = self.gitlabci.list_users()
        if resp.status_code == 200:
            print resp.content
        else:
            print "Error getting users"
            print "Server response:", resp.content

    def list_usernames(self):
        """
        Function parses/process command line args,
        and lists all the usernames on gitlab server
        """
        print '\n'.join(sorted(self.gitlabci.list_usernames()))

    def create_project(self):
        """
        Function parses/process command line args,
        and creates a project on gitlab server for
        current authenticated user
        """
        parser = argparse.ArgumentParser(
            description='Create a new project on gitlab server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the new project')

        # use -- prefix for an optional argument
        parser.add_argument(
                '-d', '--description', help='description of project')
        parser.add_argument(
                '-p', '--path', help='custom repository name for new project')
        parser.add_argument(
                '-n', '--namespace_id',
                help='namespace for the new project (defaults to user)')
        parser.add_argument(
                '-i', '--issues_enabled')
        parser.add_argument(
                '-m', '--merge_requests_enabled')
        parser.add_argument(
                '-b', '--builds_enabled')
        parser.add_argument(
                '-w', '--wiki_enabled')
        parser.add_argument(
                '-s', '--snippets_enabled')
        parser.add_argument(
                '-y', '--public',
                help='if true same as setting visibility_level = 20')
        parser.add_argument(
                '-v', '--visibility_level')
        parser.add_argument(
                '-u', '--import_url')
        parser.add_argument(
                '-l', '--public_builds')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # adding required param name to params dict
        params = {"name": args.name}

        # adding optional args to params dict
        if args.description:
            params["description"] = args.description
        if args.path:
            params["path"] = args.path
        if args.namespace_id:
            params["namespace_id"] = args.namespace_id
        if args.issues_enabled:
            params["issues_enabled"] = args.issues_enabled
        if args.merge_requests_enabled:
            params["merge_requests_enabled"] = args.merge_requests_enabled
        if args.builds_enabled:
            params["builds_enabled"] = args.builds_enabled
        if args.wiki_enabled:
            params["wiki_enabled"] = args.wiki_enabled
        if args.snippets_enabled:
            params["snippets_enabled"] = args.snippets_enabled
        if args.public:
            params["public"] = args.public
        if args.visibility_level:
            params["visibility_level"] = args.visibility_level
        if args.import_url:
            params["import_url"] = args.import_url
        if args.public_builds:
            params["public_builds"] = args.public_builds

        # creating project with params
        resp = self.gitlabci.create_project(params)
        if resp.status_code == 201:
            print "Project '%s' created" % args.name
        else:
            print "Failed to create '%s' project" % args.name
            print "Server Response: %s" % resp.content

    def create_project_for_user(self):
        """
        Function parses/process command line args,
        and creates a project on gitlab server for a give user

        ** This command needs admin credentials **
        """
        parser = argparse.ArgumentParser(
            description='Create a new project owned by user on gitlab server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('id', help='id of the user')
        parser.add_argument('project_name', help='name of the new project')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # creating repo/project with params
        resp = self.gitlabci.create_project_for_user(
                args.id, args.project_name)
        if resp.status_code == 201:
            print "Project '%s' created" % args.project_name
        else:
            print "Failed to create '%s' project" % args.project_name
            print "Server Response: %s" % resp.content

    def remove_project(self):
        """
        Function parses/process command line args,
        and removes a project from gitlab server
        """
        parser = argparse.ArgumentParser(
            description='Remove a new project from gitlab server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('proj_id', help='id of the project')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # confirm deletion from user
        confirm = confirm_yes_no(
                "Do you really want to delete project ?", "no")
        if not confirm:
            return

        # removing project
        resp = self.gitlabci.remove_project(args.proj_id)
        if resp.status_code == 200:
            print "Project removed successfully"
        else:
            print "Failed to remove project"
            print "Server Response: %s" % resp.content

    def add_ssh_key(self):
        """
        Function parses/process command line args,
        and adds a SSH key to gitlab user account
        """
        parser = argparse.ArgumentParser(
            description='Add SSH key to gitlab user account')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('title', help='title for SSH key')
        parser.add_argument('key', help='a valid ssh key')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # adding SSH key
        resp = self.gitlabci.add_ssh_key(args.title, args.key)
        if resp.status_code == 201:
            print "SSH key added successfully"
        else:
            print "Failed to add SSH key"
            print "Server Response:", resp.content

    def add_ssh_key_user(self):
        """
        Function parses/process command line args,
        and adds a SSH key to given gitlab user's account
        """
        parser = argparse.ArgumentParser(
            description='Add SSH key to gitlab user account')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('id', help='id of the specified user')
        parser.add_argument('title', help='title for SSH key')
        parser.add_argument('key', help='a valid ssh key')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # adding SSH key
        resp = self.gitlabci.add_ssh_key_user(args.id, args.title, args.key)
        if resp.status_code == 201:
            print "SSH key added successfully"
        else:
            print "Failed to add SSH key"
            print "Server Response:", resp.content

    def remove_ssh_key(self):
        """
        Function parses/process command line args and
        removes a SSH key from a gitlab user account with give id
        """
        parser = argparse.ArgumentParser(
            description='Remove a SSH key from gitlab user account')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('id', help='id of a SSH key')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # removing SSH key
        resp = self.gitlabci.remove_ssh_key(args.id)

        # ensuring server response for key removal
        if resp.status_code == 200:
            rdata = json.loads(resp.content)
            # null content in response implies that key does't exist
            if not rdata:
                print "Failed to remove SSH key, key doen't exist"
                return

            # double checking removed key id with id in server response
            if rdata["id"] == int(args.id):
                print "SSH key with title '%s' removed successfully" \
                        % rdata["title"]
        else:
            print "Failed to remove SSH key"
            print "Server Response:", resp.content

    def remove_ssh_key_for_user(self):
        """
        Function parses/process command line args and
        removes a SSH key from a gitlab user account with give id

        ** This command needs admin credentials **
        """
        parser = argparse.ArgumentParser(
            description='Remove a SSH key from gitlab user account and key id')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('uid', help='id of a gitlab user')
        parser.add_argument('kid', help='id of a SSH key')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # removing SSH key
        resp = self.gitlabci.remove_ssh_key_for_user(args.uid, args.kid)

        # ensuring server response for key removal
        if resp.status_code == 200:
            rdata = json.loads(resp.content)
            # null content in response implies that key does't exist
            if not rdata:
                print "Failed to remove SSH key, key doen't exist"
                return

            # double checking removed key id with id in server response
            if rdata["id"] == int(args.kid):
                print "SSH key with title '%s' removed successfully" \
                        % rdata["title"]
        else:
            print "Failed to remove SSH key"
            print "Server Response:", resp.content

    def add_email(self):
        """
        Function parses/process command line args,
        and adds email for current user
        """
        parser = argparse.ArgumentParser(
            description='Add email for current user')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('email', help='email to add')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        resp = self.gitlabci.add_email(args.email)
        print resp.content

    def add_email_for_user(self):
        """
        Function parses/process command line args,
        and adds email for given user id and email
        """
        parser = argparse.ArgumentParser(
            description='Add email for given user id')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('id', help='id of the user')
        parser.add_argument('email', help='email to add')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        resp = self.gitlabci.add_email_for_user(args.id, args.email)
        print resp.content

    def list_emails(self):
        """
        Function parses/process command line args,
        and lists emails for current user
        """
        resp = self.gitlabci.list_emails()
        print resp.content

    def list_emails_for_user(self):
        """
        Function parses/process command line args,
        and lists emails for user id

        Available for admin only
        """
        parser = argparse.ArgumentParser(
            description='List emails for given user id')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('id', help='id of the user')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])
        resp = self.gitlabci.list_emails_for_user(args.id)
        print resp.content

    def list_ssh_keys(self):
        """
        Function parses/process command line args,
        and adds a SSH key to gitlab user account
        """
        # getting SSH keys
        resp = self.gitlabci.list_ssh_keys()
        if resp.status_code == 200:
            rdata = json.loads(resp.content)
            for item in rdata:
                print "ID:", item["id"]
                print "Title:", item["title"]
                print "Key:", item["key"]
                print
        else:
            print "Failed to get SSH keys"
            print "Server Response:", resp.content

    def list_ssh_keys_for_user(self):
        """
        Function parses/process command line args,
        and adds a SSH key to gitlab user id

        ** This command needs admin credentials **
        """
        parser = argparse.ArgumentParser(
            description='List SSH keys for given user id')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('id', help='id of the user')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # getting SSH keys
        resp = self.gitlabci.list_ssh_keys_for_user(args.id)
        if resp.status_code == 200:
            rdata = json.loads(resp.content)
            for item in rdata:
                print "ID:", item["id"]
                print "Title:", item["title"]
                print "Key:", item["key"]
                print
        else:
            print "Failed to get SSH keys"
            print "Server Response:", resp.content

    def create_job(self):
        """
        Function parses/process command line args,
        and creates a job on jenkins server
        """
        parser = argparse.ArgumentParser(
            description='Create a new job on jenkins server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the new job')

        # use -- prefix for an optional argument
        parser.add_argument(
                '-c', '--config', help='path to config file')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # before creating job, ensure it doesn't exist
        if self.jenkinsci.job_exists(args.name):
            print "Error, Can't create job"
            print "Job '%s' already exists" % args.name
            return

        # creating job on jenkins server, if a config file is specified,
        # create the job with that configuration, otherwise, create it
        # with empty configuration
        try:
            if args.config:
                self.jenkinsci.create_job(
                        args.name, get_file_data(args.config))
            else:
                self.jenkinsci.create_empty_job(args.name)
            print "Job '%s' created successfully" % args.name
        except:
            print "Failed to create job '%s'" % args.name

    def create_view(self):
        """
        Function parses/process command line args,
        and creates a view on jenkins server
        """
        parser = argparse.ArgumentParser(
            description='Create a new view on jenkins server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the new view')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # creating view on jenkins server
        try:
            self.jenkinsci.create_empty_view(args.name)
            print "View '%s' created successfully" % args.name
        except:
            print "Failed to create view '%s'" % args.name

    def delete_view(self):
        """
        Function parses/process command line args,
        and deletes a view from jenkins server
        """
        parser = argparse.ArgumentParser(
            description='Delete a view from jenkins server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the view to delete')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # deleting a view from jenkins server
        try:
            self.jenkinsci.delete_view(args.name)
            print "View '%s' deleted successfully" % args.name
        except:
            print "Failed to delete view '%s'" % args.name

    def get_job_info(self):
        """
        Function parses/process command line args,
        and gets details of job from jenkins server
        """
        parser = argparse.ArgumentParser(
            description='Get details of a job from jenkins server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the new job')

        # use -- prefix for an optional argument
        parser.add_argument(
                '-d', '--depth', help='depth of info, eg, 1 or 2 etc')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # check that job exists
        if not self.jenkinsci.job_exists(args.name):
            print "Error, Can't get job info"
            print "Job '%s' doesn't exists" % args.name
            return

        # if depth is specified, use it, default is 0
        depth = 0
        if args.depth:
            depth = args.depth

        # getting job details from jenkins server
        print self.jenkinsci.get_job_info(args.name, depth)

    def debug_job_info(self):
        """
        Function parses/process command line args,
        and gets debug info of job from jenkins server
        """
        parser = argparse.ArgumentParser(
            description='Get debug info of a job from jenkins server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the job')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # check that job exists
        if not self.jenkinsci.job_exists(args.name):
            print "Error, Can't get job info"
            print "Job '%s' doesn't exists" % args.name
            return

        # getting job details from jenkins server
        print self.jenkinsci.debug_job_info(args.name)

    def get_queue_info(self):
        """
        Function parses/process command line args,
        and gets a queue of jenkins jobs to be done
        """
        # getting jobs' queue
        print self.jenkinsci.get_queue_info()

    def list_jobs(self):
        """
        Function returns a list of all jobs on jenkins server
        """
        jobs = self.jenkinsci.get_jobs()
        print yaml.safe_dump(jobs)

    def get_jobs_names(self):
        """
        Function returns names of all jobs on jenkins server

        Sometimes useful when you want to look for a job name,
        and pass it to some other command/operation
        """
        print '\n'.join(self.jenkinsci.get_jobs_names())

    def jobs_count(self):
        """
        Function returns a count of jobs on jenkins server
        """
        print "Jobs count:", self.jenkinsci.jobs_count()

    def enable_job(self):
        """
        Function parses/process command line args,
        and enables an existing job on jenkins server
        """
        parser = argparse.ArgumentParser(
            description='Enable a job on jenkins server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the job to enable')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # before enabling job, ensure it exists
        if not self.jenkinsci.job_exists(args.name):
            print "Error, Can't enable job"
            print "Job '%s' doesn't exist" % args.name
            return

        # enabling job on jenkins server
        self.jenkinsci.enable_job(args.name)
        print "Job '%s' enabled" % args.name

    def disable_job(self):
        """
        Function parses/process command line args,
        and disables an existing job on jenkins server
        """
        parser = argparse.ArgumentParser(
            description='Disable a job on jenkins server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the job to disable')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # before disabling job, ensure it exists
        if not self.jenkinsci.job_exists(args.name):
            print "Error, Can't disable job"
            print "Job '%s' doesn't exist" % args.name
            return

        # disabling job on jenkins server
        self.jenkinsci.disable_job(args.name)
        print "Job '%s' disable_job" % args.name

    def build_job(self):
        """
        Function parses/process command line args,
        and builds an existing job on jenkins server
        """
        parser = argparse.ArgumentParser(
            description='Builds a job on jenkins server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the job to build')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # before building job, ensure it exists
        if not self.jenkinsci.job_exists(args.name):
            print "Error, Can't build job"
            print "Job '%s' doesn't exist" % args.name
            return

        # building job on jenkins server
        self.jenkinsci.build_job(args.name)
        print "Build trigered for job '%s'" % args.name

    def rename_job(self):
        """
        Function parses/process command line args,
        and renames an existing job on jenkins server
        """
        parser = argparse.ArgumentParser(
            description='Renames a job on jenkins server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('from_name', help='name of the job to rename')
        parser.add_argument('to_name', help='new name of the job')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # before renaming job, ensure it exists
        if not self.jenkinsci.job_exists(args.from_name):
            print "Error, Can't rename job"
            print "Job '%s' doesn't exist" % args.from_name
            return

        # before renaming job to new name,
        # ensure job with to_name doesn't exist
        if self.jenkinsci.job_exists(args.to_name):
            print "Error, Can't rename job to new name"
            print "Job with name '%s' already exists" % args.to_name
            return

        # renaming job on jenkins server
        self.jenkinsci.rename_job(args.from_name, args.to_name)
        print "Job renamed successfully"

    def last_build_info(self):
        """
        Function parses/process command line args,
        and gets last build info for a job
        """
        parser = argparse.ArgumentParser(
            description='Get last build info for a job on jenkins server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the job to get build info')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # before getting last build info, ensure the job exists
        if not self.jenkinsci.job_exists(args.name):
            print "Error, Can't get last build info"
            print "Job '%s' doesn't exist" % args.name
            return

        # getting last build info
        print self.jenkinsci.get_last_build_info(args.name)

    def delete_job(self):
        """
        Function parses/process command line args,
        and deletes an existing job on jenkins server
        """
        parser = argparse.ArgumentParser(
            description='Deletes a job on jenkins server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the job to delete')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # before deleting job, ensure it exists
        if not self.jenkinsci.job_exists(args.name):
            print "Error, Can't delete job"
            print "Job '%s' doesn't exist" % args.name
            return

        # confirm deletion from user
        confirm = confirm_yes_no(
                "Do you really want to delete this job ?", "no")
        if not confirm:
            return

        # deleting job on jenkins server
        self.jenkinsci.delete_job(args.name)
        print "Job '%s' deleted successfully" % args.name

    def get_plugins(self):
        """
        Function parses/process command line args,
        and retrieves information about all the installed plugins
        on the jenkins server
        """
        parser = argparse.ArgumentParser(
            description='Get info all installed plugins on jenkins server')

        # use -- prefix for an optional argument
        parser.add_argument(
                '-d', '--depth', help='depth of info, eg, 1 or 2 etc')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # if depth is specified, use it, default is 2
        depth = 2
        if args.depth:
            depth = args.depth

        # getting jenkins' plugins' info
        print self.jenkinsci.get_plugins(depth)

    def get_plugin_info(self):
        """
        Function parses/process command line args,
        and retrieves information about jenkins plugin
        with the given name
        """
        parser = argparse.ArgumentParser(
            description='Get info all installed plugins on jenkins server')

        # for not optional arguments, dont use -- prefix
        parser.add_argument('name', help='name of the job to delete')

        # use -- prefix for an optional argument
        parser.add_argument(
                '-d', '--depth', help='depth of info, eg, 1 or 2 etc')

        # parse args for this command
        args = parser.parse_args(sys.argv[2:])

        # if depth is specified, use it, default is 2
        depth = 2
        if args.depth:
            depth = args.depth

        # getting jenkins' plugins' info
        info = self.jenkinsci.get_plugin_info(args.name, depth)
        if not info:
            print "No info found for plugin '%s'" % args.name
            return
        print info

    def get_plugin_names(self):
        """
        Function parses/process command line args and
        shows names all installed plugins on jenkins server
        """
        print '\n'.join(sorted(self.jenkinsci.get_plugin_names()))


if __name__ == "__main__":
    OpenCI()
