
import sys
import threading
from queue import Queue, Empty
import traceback
import time
from .exceptions import *
from django.utils import timezone
from .models import Job

# exceptions
class NoResultsPending(Exception):
    """All work requests have been processed."""
    pass

class NoWorkersAvailable(Exception):
    """No worker threads available to process remaining requests."""
    pass


# internal module helper functions
def _handle_thread_exception(request, exc_info):
    """Default exception handler callback function.
    This just prints the exception info via ``traceback.print_exception``.
    """
    traceback.print_exception(*exc_info)


# utility functions
def makeRequests(callable_, args_list, callback=None,
        exc_callback=_handle_thread_exception):
    """Create several work requests for same callable with different arguments.
    Convenience function for creating several work requests for the same
    callable where each invocation of the callable receives different values
    for its arguments.
    ``args_list`` contains the parameters for each invocation of callable.
    Each item in ``args_list`` should be either a 2-item tuple of the list of
    positional arguments and a dictionary of keyword arguments or a single,
    non-tuple argument.
    See docstring for ``WorkRequest`` for info on ``callback`` and
    ``exc_callback``.
    """
    requests = []
    for item in args_list:
        if isinstance(item, tuple):
            requests.append(
                WorkRequest(callable_, item[0], item[1], callback=callback,
                    exc_callback=exc_callback)
            )
        else:
            requests.append(
                WorkRequest(callable_, [item], None, callback=callback,
                    exc_callback=exc_callback)
            )
    return requests


# classes
class WorkerThread(threading.Thread):
    """Background thread connected to the requests/results queues.
    A worker thread sits in the background and picks up work requests from
    one queue and puts the results in another.
    """

    def __init__(self, requests_queue, results_queue, poll_timeout=5, **kwargs):
        """Set up thread in daemonic mode and start it immediatedly.
        ``requests_queue`` and ``results_queue`` are instances of
        ``Queue.Queue`` passed by the ``ThreadPool`` class when it creates a new
        worker thread.
        """
        threading.Thread.__init__(self, **kwargs)
        self.daemon = True
        self._requests_queue = requests_queue
        self._results_queue = results_queue
        self._poll_timeout = poll_timeout
        self.start()

    def run(self):
        """Repeatedly process the job queue until told to exit."""
        while True:
            try:
                # poll the request queue
                request = self._requests_queue.get(True, self._poll_timeout)
            except Empty:
                continue
            else:
                try:
                    result = request.callable(*request.args, **request.kwargs)
                    self._results_queue.put((request, result))
                except:
                    request.exception = True
                    self._results_queue.put((request, sys.exc_info()))
                finally:
                    JobRunner().release_job(request.requestID)




class WorkRequest:
    """A request to execute a callable for putting in the request queue later.
    See the module function ``makeRequests`` for the common case
    where you want to build several ``WorkRequest`` objects for the same
    callable but with different arguments for each call.
    """

    def __init__(self, callable_, args=None, kwargs=None, requestID=None,
            callback=None, exc_callback=_handle_thread_exception):
        """Create a work request for a callable and attach callbacks.
        A work request consists of the a callable to be executed by a
        worker thread, a list of positional arguments, a dictionary
        of keyword arguments.
        A ``callback`` function can be specified, that is called when the
        results of the request are picked up from the result queue. It must
        accept two anonymous arguments, the ``WorkRequest`` object and the
        results of the callable, in that order. If you want to pass additional
        information to the callback, just stick it on the request object.
        You can also give custom callback for when an exception occurs with
        the ``exc_callback`` keyword parameter. It should also accept two
        anonymous arguments, the ``WorkRequest`` and a tuple with the exception
        details as returned by ``sys.exc_info()``. The default implementation
        of this callback just prints the exception info via
        ``traceback.print_exception``. If you want no exception handler
        callback, just pass in ``None``.
        ``requestID``, if given, must be hashable since it is used by
        ``ThreadPool`` object to store the results of that work request in a
        dictionary. It defaults to the return value of ``id(self)``.
        """
        if requestID is None:
            self.requestID = id(self)
        else:
            try:
                self.requestID = hash(requestID)
            except TypeError:
                raise TypeError("requestID must be hashable.")
        self.exception = False
        self.callback = callback
        self.exc_callback = exc_callback
        self.callable = callable_
        self.args = args or []
        self.kwargs = kwargs or {}

    def __str__(self):
        return "<WorkRequest id=%s args=%r kwargs=%r exception=%s>" % \
            (self.requestID, self.args, self.kwargs, self.exception)


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


@singleton
class ThreadPool(threading.Thread):
    """A thread pool, distributing work requests and collecting results.
    See the module docstring for more information.
    """

    def __init__(self, num_workers, q_size=0, resq_size=0, poll_timeout=5):
        """Set up the thread pool and start num_workers worker threads.
        ``num_workers`` is the number of worker threads to start initially.
        If ``q_size > 0`` the size of the work *request queue* is limited and
        the thread pool blocks when the queue is full and it tries to put
        more work requests in it (see ``putRequest`` method), unless you also
        use a positive ``timeout`` value for ``putRequest``.
        If ``resq_size > 0`` the size of the *results queue* is limited and the
        worker threads will block when the queue is full and they try to put
        new results in it.
        .. warning:
            If you set both ``q_size`` and ``resq_size`` to ``!= 0`` there is
            the possibilty of a deadlock, when the results queue is not pulled
            regularly and too many jobs are put in the work requests queue.
            To prevent this, always set ``timeout > 0`` when calling
            ``ThreadPool.putRequest()`` and catch ``Queue.Full`` exceptions.
        """
        super().__init__()
        self._requests_queue = Queue(q_size)
        self._results_queue = Queue(resq_size)
        self.workers = []
        self.workRequests = {}
        self.createWorkers(num_workers, poll_timeout)

    def createWorkers(self, num_workers, poll_timeout=5):
        """Add num_workers worker threads to the pool.
        ``poll_timout`` sets the interval in seconds (int or float) for how
        ofte threads should check whether they are dismissed, while waiting for
        requests.
        """
        for i in range(num_workers):
            self.workers.append(WorkerThread(self._requests_queue,
                self._results_queue, poll_timeout=poll_timeout))

    def putRequest(self, request, block=True, timeout=None):
        """Put work request into work queue and save its id for later."""
        assert isinstance(request, WorkRequest)
        # don't reuse old work requests
        assert not getattr(request, 'exception', None)
        self._requests_queue.put(request, block, timeout)
        self.workRequests[request.requestID] = request

    def poll(self, block=False):
        """Process any new results in the queue."""
        while True:
            # still results pending?
            if not self.workRequests:
                raise NoResultsPending
            # are there still workers to process remaining requests?
            elif block and not self.workers:
                raise NoWorkersAvailable
            try:
                # get back next results
                request, result = self._results_queue.get(block=block)
                # has an exception occured?
                if request.exception and request.exc_callback:
                    request.exc_callback(request, result)
                # hand results to callback, if any
                if request.callback and not (request.exception and request.exc_callback):
                    request.callback(request, result)
                del self.workRequests[request.requestID]
            except Exception as e:
                break

    def wait(self):
        """Wait for results, blocking until all have arrived."""
        while 1:
            try:
                self.poll(True)
            except NoResultsPending:
                break

    def run(self):
        while True:
            try:
                time.sleep(0.5)
                self.poll()
            except KeyboardInterrupt:
                print("**** Interrupted!")
                break
            except NoResultsPending:
                continue


@singleton
class JobRunner:
    def __init__(self):
        self.thread_pool = ThreadPool(10)
        self.thread_pool.start()
        self.active_tasks = {}

    def run_job(self, task_id):
        if task_id in self.active_tasks.values():
            raise JobAlreadyRunningException()
        else:
            try:
                job = Job.objects.filter(pk=task_id).first()
                if job:
                    job.status = Job.STATUS_RUNNING
                    job.last_executed = timezone.now()
                    job.save()
                    work_request = WorkRequest(exec, [job.document])
                    self.active_tasks.update({work_request.requestID: task_id})
                    self.thread_pool.putRequest(work_request)
                else:
                    raise JobNotFoundException
            except JobNotFoundException as e:
                pass
            except JobAlreadyRunningException as e:
                pass
            except Exception as e:
                job.status = Job.STATUS_FAILED
                job.save()
                self.active_tasks = {k: v for k, v in self.active_tasks.items() if v != task_id}
                traceback.print_exception(e)

    def release_job(self, request_id):
        if request_id not in self.active_tasks.keys():
            pass
        else:
            job_id = self.active_tasks[request_id]
            Job.objects.filter(pk=job_id).update(status=Job.STATUS_READY)
            try:
                del self.active_tasks[request_id]
            except KeyError:
                pass


