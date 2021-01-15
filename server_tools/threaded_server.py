import traceback

from twisted.internet import defer, reactor, threads
from twisted.internet.defer import inlineCallbacks, returnValue

from labrad.concurrent import futures
from labrad.server import LabradServer


class ThreadedServer(LabradServer):
    """A LabRAD server that dispatches requests to a thread pool."""

    def __init__(self, pool=None):
        """Create a new threaded server.

        Requests and lifecycle methods like initServer will be executed on a
        thread pool instead of in the twisted reactor thread. In addition,
        accessing self.client from a thread other than the reactor thread will
        return a synchronous labrad.client.Client object.

        Args:
            pool (None | concurrent.futures.ThreadPoolExecutor):
                Thread pool instance to use for server lifecycle methods and
                request handling. If None, use the default twisted threadpool,
                which maxes out at 10 threads.
        """
        super(ThreadedServer, self).__init__()
        self.__pool = pool

    @inlineCallbacks
    def _dispatch(self, func, *args, **kw):
        if self.__pool is None:
            result = yield threads.deferToThread(self._exception_handler(func), *args, **kw)
        else:
            result = self.__pool.submit(func, *args, **kw)
        while isinstance(result, futures.Future):
            result = yield labrad.concurrent.future_to_deferred(result)
        returnValue(result)

    def _exception_handler(self, func):
        def wrapped_func(*args, **kw):
            try:
                return func(*args, **kw)
            except:
                traceback.print_exc()
                raise
        return wrapped_func

