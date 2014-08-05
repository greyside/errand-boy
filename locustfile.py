import itertools
import time

from locust import Locust, events, task, TaskSet

from errand_boy.transports.unixsocket import UNIXSocketTransport


def capture(func):
    name = func.func_name
    
    def wrapper(self, cmd, *args, **kwargs):
        start_time = time.time()
        
        response = None
        successful = True
        e = None
        try:
            response = func(self, cmd, *args, **kwargs)
        except Exception as e:
            pass
        
        total_time = int((time.time() - start_time) * 1000)
        
        if e is None:
            response_length = len(response[1]) + len(response[2])
            
            events.request_success.fire(request_type=name, name=cmd, response_time=total_time, response_length=response_length)
        else:
            events.request_failure.fire(request_type=name, name=cmd, response_time=total_time, exception=e)
            raise e
        
        return response
    return wrapper

class CustomUNIXSocketTransport(UNIXSocketTransport):
    run_cmd = capture(UNIXSocketTransport.run_cmd)


class ErrandBoyLocust(Locust):
    def __init__(self, *args, **kwargs):
        super(ErrandBoyLocust, self).__init__(*args, **kwargs)
        self.client = CustomUNIXSocketTransport()


class LoadTestTask(TaskSet):
    @task
    def run_cmd_ls(self):
        response = self.client.run_cmd('ls -al')
    
    @task
    def run_cmd_date(self):
        response = self.client.run_cmd('date')


class LoadTestUser(ErrandBoyLocust):
    task_set = LoadTestTask
    min_wait = 0
    max_wait = 0
