#
# script for patched/mocked functions with
# params and expected sane responses
#

import json


class Response:
    pass


##########################################################
#                                                        #
# MOCKED FUNCTIONS FOR HTTP GET/POST FOR REQUESTS MODULE #
#                                                        #
##########################################################
def post(url, data, headers):
    """
    patching a general request post on a given url with
    specified data and headers
    """
    print "[INFO] :: running mocked post on %s" % url
    resp = Response()
    resp.status_code = 201
    resp.content = "OK"
    return resp


def get(url, headers):
    """
    patching a general requests' get() with a given url
    """
    print "[INFO] :: running mocked get on %s" % url
    resp = Response()
    resp.status_code = 200
    resp.content = "OK"
    return resp

def post_create_user(url, data, headers):
    """
    patching a general request post on a given url with
    specified data and headers
    """
    print "[INFO] :: running mocked post on %s" % url
    resp = Response()
    resp.status_code = 201

    # some dummy id to be of newly created user
    resp.content = json.dumps({"id": 1})
    return resp

##########################################################
#                                                        #
#         MOCKED FUNCTIONS FOR JENKINS                   #
#                                                        #
##########################################################

# dummy lists for test jobs' data
mocked_test_jobs = []
mocked_disabled_jobs = []


def mocked_job_exists(job_name):
    """
    Function to patch job_exists() function of jenkins
    """
    print "[MOCK] mocked_job_exists() checking job", job_name
    return job_name in mocked_test_jobs


def mocked_create_job(job_name, config=None):
    """
    Function to patch create_job() function of jenkins
    """
    print "[MOCK] mocked_create_job() checking job '%s' exists ?" % job_name
    if job_name in mocked_test_jobs:
        raise Exception
    mocked_test_jobs.append(job_name)


def mocked_rename_job(from_name, to_name):
    """
    Function to patch rename_job() function of jenkins
    """
    print "[MOCK] mocked_rename_job() from %s to %s" % (from_name, to_name)
    if from_name in mocked_test_jobs:
        mocked_test_jobs.remove(from_name)
    if not to_name in mocked_test_jobs:
        mocked_test_jobs.append(to_name)


def mocked_delete_job(job_name):
    """
    Function to patch delete_job() function of jenkins
    """
    print "[MOCK] mocked_delete_job() deleting job", job_name
    if job_name in mocked_test_jobs:
        mocked_test_jobs.remove(job_name)


def mocked_disable_job(job_name):
    """
    Function to patch disable_job() function of jenkins
    """
    print "[MOCK] mocked_disable_job() disabling job", job_name
    if not job_name in mocked_disabled_jobs:
        mocked_disabled_jobs.append(job_name)


def mocked_enable_job(job_name):
    """
    Function to patch enable_job() function of jenkins
    """
    print "[MOCK] mocked_enable_job() enabling job", job_name
    if job_name in mocked_disabled_jobs:
        mocked_disabled_jobs.remove(job_name)


def mocked_get_job_info(job_name, depth=0):
    """
    Function to patch get_job_info() function of jenkins
    """
    print "[MOCK] mocked_get_job_info() getting job info of", job_name
    if job_name in mocked_disabled_jobs:
        return {"color": "disabled"}
    return {"color": "enabled"}

def mocked_get_jobs():
    return mocked_test_jobs

def mocked_get_plugins(depth=2):
    """
    FIXME dont use dummy values in future !!!
    """
    return ['plugin 1', 'plugin 2']
