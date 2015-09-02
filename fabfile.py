from fabric.api import env, local
from fabric.decorators import runs_once


env.forward_agent = True

env.hosts = []


@runs_once
def locust_local(url=None):
    # ignored
    test_host = 'http://127.0.0.1'

    locust_class = 'LoadTestUser'

    local('locust --host {} {}'.format(test_host, locust_class))
