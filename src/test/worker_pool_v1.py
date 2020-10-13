from queue import Queue
from threading import Thread, Event
from time import sleep


# default handler
def default_handler(name, exception, *args, **kwargs):
    print('%s raised %s with args %s and kwargs %s' % (name, str(exception), repr(args), repr(kwargs)))
    pass


# class for workers
class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""

    def __init__(self, name, queue, results, abort, idle, exception_handler):
        Thread.__init__(self)
        self.name = name
        self.queue = queue
        self.results = results
        self.abort = abort
        self.idle = idle
        self.exception_handler = exception_handler
        self.daemon = True
        self.start()

    """Thread work loop calling the function with the params"""

    def run(self):
        # keep running until told to abort
        while not self.abort.is_set():
            try:
                # get a task and raise immediately if none available
                func, args, kwargs = self.queue.get(False)
                self.idle.clear()
            except:
                self.idle.set()
                continue

            try:
                # the function may raise
                result = func(*args, **kwargs)
                if (result is not None):
                    self.results.put(result)
            except Exception as e:
                # so we move on and handle it in whatever way the caller wanted
                self.exception_handler(self.name, e, args, kwargs)
            finally:
                # task complete no matter what happened
                self.queue.task_done()


# class for thread pool
class Pool:
    """Pool of threads consuming tasks from a queue"""

    def __init__(self, thread_count, batch_mode=False, exception_handler=default_handler):
        # batch mode means block when adding tasks if no threads available to process
        self.queue = Queue(thread_count if batch_mode else 0)
        self.resultQueue = Queue(0)
        self.thread_count = thread_count
        self.exception_handler = exception_handler
        self.aborts = []
        self.idles = []
        self.threads = []

    """Tell my threads to quit"""

    def __del__(self):
        self.abort()

    """Start the threads, or restart them if you've aborted"""

    def run(self, block=False):
        # either wait for them to finish or return false if some arent
        if block:
            while self.alive():
                sleep(1)
        elif self.alive():
            return False

        # go start them
        self.aborts = []
        self.idles = []
        self.threads = []
        for n in range(self.thread_count):
            abort = Event()
            idle = Event()
            self.aborts.append(abort)
            self.idles.append(idle)
            self.threads.append(
                Worker('thread-%d' % n, self.queue, self.resultQueue, abort, idle, self.exception_handler))
        return True

    """Add a task to the queue"""

    def enqueue(self, func, *args, **kargs):
        self.queue.put((func, args, kargs))

    """Wait for completion of all the tasks in the queue"""

    def join(self):
        self.queue.join()

    """Tell each worker that its done working"""

    def abort(self, block=False):
        # tell the threads to stop after they are done with what they are currently doing
        for a in self.aborts:
            a.set()
        # wait for them to finish if requested
        while block and self.alive():
            sleep(1)

    """Returns True if any threads are currently running"""

    def alive(self):
        return True in [t.is_alive() for t in self.threads]

    """Returns True if all threads are waiting for work"""

    def idle(self):
        return False not in [i.is_set() for i in self.idles]

    """Returns True if not tasks are left to be completed"""

    def done(self):
        return self.queue.empty()

    """Get the set of results that have been processed, repeatedly call until done"""

    def results(self, wait=0):
        sleep(wait)
        results = []
        try:
            while True:
                # get a result, raises empty exception immediately if none available
                results.append(self.resultQueue.get(False))
                self.resultQueue.task_done()
        except:
            pass
        return results


# Handler
def work(x):
    sleep(5)
    print('%d finished' % x)
    return x


def wait_for_results(p):
    while not p.done() or not p.idle():
        for result in p.results():
            print('got result %s' % str(result))
    for result in p.results():
        print('got result %s' % str(result))


if __name__ == '__main__':

    p = Pool(3)
    print('queueing work')
    for i in range(10):
        p.enqueue(work, i)

    print('starting work')
    p.run(True)

    print('waiting')
    sleep(8)
    for result in p.results():
        print('got result %s' % str(result))

    print('cancel unstarted work')
    p.abort()

    print('waiting and restarting')
    p.run(True)

    print('restarted waiting for results')
    wait_for_results(p)

    print('adding more work')
    for i in range(10, 17):
        p.enqueue(work, i)
    wait_for_results(p)
