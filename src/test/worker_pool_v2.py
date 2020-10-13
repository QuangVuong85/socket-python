from queue import Queue, Empty
from threading import Thread, RLock as rLock
import logging
import time

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class _WorkerThread(Thread):
    def __init__(self, task_queue, thread_name, polling_timeout):
        super(_WorkerThread, self).__init__(name=thread_name)
        self.__task_queue = task_queue
        """ :type : Queue """
        self.__terminated = False
        """ :type : bool """
        self.__thread_name = thread_name
        """ :type : str """
        self.__polling_timeout = polling_timeout
        """ :type : int """

    def run(self):
        while not self.__terminated:
            # locking implemented by the Queue class
            # blocks until a task is queued
            task = None
            try:
                task = self.__task_queue.get(timeout=self.__polling_timeout)
            except Empty:
                pass

            if task is not None:
                if isinstance(task, AbstractRunnable):
                    try:
                        task.execute()
                    except BaseException as ex:
                        log.info("Caught exception while executing task : %s: %s" % (ex.__class__.__name__, ex))
                        # traceback.print_exc()

                    # notify the queue that the task is done
                    self.__task_queue.task_done()
                else:
                    # this should not happen!
                    log.error("Invalid object enqueued to task list.")

        log.debug("Terminating worker thread %s" % self.__thread_name)

    def terminate(self):
        self.__terminated = True


class ThreadPool(object):
    """
    The ThreadPool class offers a simple Thread pool implementation for Python. It uses Python's Queues to coordinate
    tasks among a set of worker threads. The specified number of threads are created when the thread pool is created,
    and is maintained so that they do not increase more than that number.
    """

    def __init__(self, size, name, daemon=False, polling_timeout=60):
        """
        Creates a ThreadPool object.
        :param int size: The size of the Thread Pool. This should be a value larger than zero. If a value less than
        1 is passed, a ValueError will be raised.
        :param str name: An identifying name for the ThreadPool. All the worker threads will share this name as a part
         of their thread names.
        :param bool daemon: Set this to True if the worker threads should immediately terminate when the main thread
        terminates.
        :param int polling_timeout: The polling timeout for the worker threads when waiting for tasks. This should be
        a value larger than zero. The Polling timeout determines the timeout value when waiting on a get() request on
         the task queue. This value directly affects the time it takes for the worker threads to terminate when
         terminate() is called on the Thread Pool.
        :return:
        """
        if size < 1:
            raise ValueError("Thread pool size should be more than 0")

        if polling_timeout < 1:
            raise ValueError("Polling timeout should be more than 0")

        self.__task_queue = Queue()
        """ :type : Queue """
        self.__pool_size = size
        """ :type : int """
        self.__pool_name = name
        """ :type : str """
        self.__worker_threads = []
        """ :type : list """
        self.__polling_timeout = polling_timeout
        """ :type : int """
        self.__daemon = daemon
        """ :type : bool """""

        self._create_worker_threads()

    def enqueue(self, task):
        """
        Adds the specified task to the task queue for a worker thread to start working on it. If any free worker
        threads are waiting on the task queue, it will immediately pick up this task.
        :param task: The task to be added to the task queue.
        :type task: :class: `breadpool.pool.AbstractRunnable` instance
        :return:
        """
        if not isinstance(task, AbstractRunnable):
            raise ValueError("The task must be of AbstractRunnable or a subclass of it.")

        # thread safety comes from Queue class
        self.__task_queue.put(task)

    def get_pool_size(self):
        """
        Returns the size of the thread pool.
        :return: The size of the thread pool
        :rtype: int
        """
        with rLock():
            return self.__pool_size

    def terminate(self):
        """
        Waits for the task queue to finish and sends the terminate event for all the worker threads.
        :return:
        """
        with rLock():
            log.debug("Waiting until all the tasks are done")
            self.__task_queue.join()
            log.debug("Sending termination signal for the worker threads")
            for worker_thread in self.__worker_threads:
                worker_thread.terminate()

    def _create_worker_threads(self):
        with rLock():
            while len(self.__worker_threads) < self.__pool_size:
                thread_name = "%s-%s" % (self.__pool_name, (len(self.__worker_threads) + 1))
                worker_thread = _WorkerThread(self.__task_queue, thread_name, self.__polling_timeout)
                worker_thread.setDaemon(self.__daemon)
                worker_thread.start()
                self.__worker_threads.append(worker_thread)


class ScheduledJobExecutor(Thread):
    """
    A Scheduled executor which periodically executes a given task. This should be given a thread pool to work on.
    When a task is submitted to the scheduled task, it will repeatedly, periodically execute that task using the
    provided thread pool.
    """

    def __init__(self, task, thread_pool, delay, name):
        """
        Creates a ScheduledJobExecutor instance.
        :param task: The task to be repeatedly executed.
        :type task: :class: `breadpool.pool.AbstractRunnable` instance
        :param thread_pool: The pool of worker threads to work on
        :type thread_pool: :class: `breadpool.pool.ThreadPool` instance
        :param int delay: The interval in seconds.
        :param str name: The name for the scheduled executor
        :return:
        """
        super(ScheduledJobExecutor, self).__init__()

        if not isinstance(task, AbstractRunnable):
            raise ValueError("The task must be of AbstractRunnable or a subclass of it.")

        if not isinstance(thread_pool, ThreadPool):
            raise ValueError("The thread_pool must be type of breadpool.pool.ThreadPool")

        if delay < 1:
            raise ValueError("The delay should be more than zero.")

        self.__task = task
        """ :type : AbstractRunnable """
        self.__thread_pool = thread_pool
        """ :type : ThreadPool  """
        self.__delay = delay
        """ :type : int """
        self.__terminated = False
        """ :type : bool """
        self.__name = name
        """ :type : str """

        self.setName(name)

    def run(self):
        # start job
        while not self.__terminated:
            start_time = time.time()
            with rLock():
                # sleep for the required duration if lock acquisition took time
                if not self.__terminated:
                    lock_end_time = time.time()
                    remaining_wait_time = self.__delay - (lock_end_time - start_time)
                    if remaining_wait_time > 0.0:
                        time.sleep(remaining_wait_time)

                    if not self.__terminated:
                        self.__thread_pool.enqueue(self.__task)

    def terminate(self):
        """
        Sets the terminate event on the scheduled executor
        :return:
        """
        with rLock():
            self.__terminated = True
            self.__thread_pool.terminate()


class AbstractRunnable(object):
    """
    The tasks that should be executed using the ThreadPool or the ScheduledJobExecutor should be of a sub class of
    AbstractRunnable. Extend AbstractRunnable and write the task implementation inside the execute() method.
    Take a look at the EasyTask implementation of AbstractRunnable for an example.
    """

    def __init__(self):
        raise NotImplementedError

    def execute(self):
        raise NotImplementedError


class EasyTask(AbstractRunnable):
    """
    This is an implementation of the AbstractRunnable class which accepts a function to be executed.
    EasyTask allows to easily submit functions as runnable tasks to the ThreadPool or the ScheduledJobExecutor.
    """

    def execute(self):
        """
        Executes the given function passing the given arguments and keyword arguments to the function
        :return:
        """
        log.debug("Executing [function] %s" % self.function.__name__)
        self.function(*self.args, **self.kwargs)

    def __init__(self, function, *args, **kwargs):
        """
        Creates an EasyTask instance wrapping the given function. If the function isn't callable a ValueError will be
        thrown.
        :param function: The function to be executed.
        :param args:
        :param kwargs:
        :return:
        """
        if not hasattr(function, '__call__'):
            raise ValueError("The task is not a valid function")

        self.function = function
        self.args = args
        self.kwargs = kwargs


'''
    Test
'''


def main():
    import random
    import threading

    def wait_test_task():
        time.sleep(random.randint(1, 3))

    def print_all_active_threads():
        live_threads = threading.enumerate()
        for live_thread in live_threads:
            print(live_thread.name)

    thread_pool = ThreadPool(5, "TestScheduledExecutorThreadLimit", polling_timeout=60, daemon=True)
    scheduled_executor = ScheduledJobExecutor(
        EasyTask(wait_test_task),
        thread_pool,
        1,
        "TestThreadLimitScheduledExecutor"
    )

    scheduled_executor.start()
    time.sleep(2)

    print_all_active_threads()
    assert threading.activeCount() == (5 + 1 + 1)  # worker threads + main thread + scheduled executor thread
    scheduled_executor.terminate()


if __name__ == '__main__':
    main()
