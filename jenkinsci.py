import jenkins


class JenkinsCI:
    """
    Class for performing various operations with jenkins
    like create jobs, web hooks, builds schedules etc.

    References:-
     * https://jenkinsapi.readthedocs.org/en/latest/
     * https://python-jenkins.readthedocs.org/en/latest/index.html
     * http://python-jenkins.readthedocs.org/en/latest/api.html
    """
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password

        self.server = jenkins.Jenkins(
                self.url, username=self.username, password=self.password)

    def get_version(self):
        """
        Function returns the Jenkins server version.
        """
        return self.server.get_version()

    def get_jobs(self):
        """
        Function returns all the jobs of Jenkins server.
        """
        return self.server.get_jobs()

    def get_jobs_names(self):
        """
        Function returns names of all the jobs on jenkins server
        """
        return [job["name"] for job in self.server.get_jobs()]

    def get_job_info(self, name, depth=0):
        """
        Function returns a python dictionary containing job info

        depth params is used for getting more details for information
        """
        return self.server.get_job_info(name, depth)

    def debug_job_info(self, job_name):
        """
        Function prints job info for give njob name
        """
        return self.server.debug_job_info(job_name)

    def get_queue_info(self):
        """
        Function returns a python list of job dictionaries
        """
        return self.server.get_queue_info()

    def get_all_jobs(self, folder_depth=None):
        """
        Function gets a list of all jobs recursively to the given folder depth.

        Each job is a dictionary with name, url, color and fullname keys.

        Parameter folder_depth is the number of levels to search, int.
        By default None, which will search all levels. 0 limits to toplevel.
        """
        return self.self.get_all_jobs(folder_depth)

    def is_job_disabled(self, name):
        """
        Function returns True if a job is disabled,
        False otherwise
        """
        # FIXME dont check job color field !!!
        return self.get_job_info(name)["color"] == "disabled"

    def jobs_count(self):
        """
        Function returns the count of jobs on jenkins server
        """
        return self.server.jobs_count()

    def job_exists(self, name):
        """
        Function returns:
            True if a job exists on jenkins server,
            False otherwise
        """
        return self.server.job_exists(name)

    def create_empty_job(self, name):
        """
        Function creates a job on jenkins server with empty config
        """
        self.server.create_job(name, jenkins.EMPTY_CONFIG_XML)

    def create_job(self, name, config_xml):
        """
        Function creates a job on jenkins server with given config xml

        config_xml is the python string containing config's xml
        """
        self.server.create_job(name, config_xml)

    def create_empty_view(self, name):
        """
        Function creates a view on jenkins server with empty config
        """
        self.server.create_view(name, jenkins.EMPTY_VIEW_CONFIG_XML)

    def delete_view(self, name):
        """
        Function deletes a view from jenkins server
        """
        self.server.delete_view(name)

    def enable_job(self, name):
        """
        Function enables a job of given name on jenkins server
        """
        self.server.enable_job(name)

    def disable_job(self, name):
        """
        function disables a job of given name on jenkins server
        """
        self.server.disable_job(name)

    def build_job(self, name):
        """
        function builds a job of given name on jenkins server
        """
        self.server.build_job(name)

    def get_running_builds(self):
        """
        function get list of all running builds on jenkins server
        """
        self.server.get_running_builds()

    def rename_job(self, from_name, to_name):
        """
        Function renames an existing Jenkins job
        """
        if from_name == to_name:
            raise Exception("to name cant be same as from")
        self.server.rename_job(from_name, to_name)

    def get_last_build_info(self, name):
        """
        Function gets last build info of a job for given name
        """
        last = self.server.get_job_info(name)['lastCompletedBuild']['number']
        return self.server.get_job_info(name, last)

    def delete_job(self, name):
        """
        Function delete a job of given name on jenkins server
        """
        self.server.delete_job(name)

    def get_plugins(self, depth=2):
        """
        Function retrieves information about all the installed plugins
        """
        return self.server.get_plugins(depth)

    def get_plugin_info(self, name, depth=2):
        """
        Function retrieves information about a plugin with given name

        depth params is used for getting more details for information
        """
        return self.server.get_plugin_info(name, depth)

    def get_plugin_names(self):
        """
        Function returns a python list containig names of
        all installed plugins on jenkins server
        """
        return [n for s, n in self.server.get_plugins().keys()]
