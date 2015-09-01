import owncloud
import threading
import Queue
from smashbox.script import config

class pyocclient_wrapper(object):
    """
    Simple wrapper over pyocclient : Client class

    If username and password are passed in the constructor, the client will try to login
    automatically, otherwise you'll need to login later

    There are 2 basic methods: "do_action" and "do_action_async". Both methods do calls a
    client method of your choice with the specific parameters.
    The do_action method will execute the action and return the result (no exception is
    catched, so exceptions might be thrown depending on the method called)
    The do_action_async method will execute the action asynchronously (creating a new thread
    and starting it)

    There are additional methods to help with the tests
    """

    def __init__(self, url, username=None, password=None, **kwargs):
        """
        Create a new instance setting the url for the client to connect. Any additional
        parameter you want to pass to the client can be pass through the kwargs param.

        If you don't pass the username and password, you'll need to make a login request
        at some point

        :param url: the url where the pyocclient will connect
        :param username: the username to login
        :param password: the password to login
        """
        client = owncloud.Client(url, **kwargs)
        if username != None and password != None:
            client.login(username, password)
        self._client = client

    def do_action(self, method, *args, **kwargs):
        """
        Execute the "method" with the appropiate parameters and return the result.
        Exceptions might be thrown depending on the called method.

        :param method: method to be called in the wrapped pyocclient, as a string. The
        method should exists
        :param args: arguments to be passed to the method
        :param kwargs: arguments to be passed to the method
        :returns: whatever the called method returns
        """
        caller = getattr(self._client, method)
        return caller(*args, **kwargs)

    def do_action_async(self, method, *args, **kwargs):
        """
        Execute the "method" with the appropiate parameters in an async way. A thread will
        be spawned to do the job.

        The method returns a tuple with:
        * A thread, to control the execution (mainly to know when the thread finishes)
        * A queue, to read the result when the thread finishes)

        The queue to read the result is an instance of Queue.Queue. It can contains the
        method's result or the exception thrown by the method (if it was raised). It's
        recommended to check the type of the result before making any assumption about
        the success or failure of the called method

        :param method: method to be called in the wrapper pyocclient
        :param args: arguments to be passed to the method
        :param kwargs: arguments to be passed to the method
        :returns: tuple with a thread and a queue objects
        """
        def caller_wrapper(method, q, *args, **kwargs):
            try:
                q.put(method(*args, **kwargs))
            except Exception as e:
                q.put(e)

        caller = getattr(self._client, method)
        result_queue = Queue.Queue()
        caller_wrapper_args = (caller, result_queue) + args
        thread = threading.Thread(target=caller_wrapper, args=caller_wrapper_args, kwargs=kwargs)
        thread.start()
        return (thread, result_queue)

    def check_filesize(self, path, size):
        """
        Check the size of the file and return True if matches. The size is checked with
        whatever the profind call returns.

        If the file isn't found (404 error code) it will return False. For other exceptions,
        they will be rethrown

        :param path: the remote path fo the file
        :param size: the size we want to check
        :returns: True if the size matches, False otherwise
        """
        try:
            info = self.do_action('file_info', path)
            return False if info is None else size == info.get_size()
        except owncloud.ResponseError as e:
            if e.status_code == 404:
                return False
            else:
                raise e

    def check_file_exists(self, path):
        """
        Check if the file exists (based on the 'file_info' call). Returns True if we get
        some info, False otherwise (including 404 error). Exceptions other than the 404
        will be rethrown

        :param path: the path to check
        :returns: True if the file exists, false otherwise
        """
        try:
            info = self.do_action('file_info', path)
            return False if info is None else True
        except owncloud.ResponseError as e:
            if e.status_code == 404:
                return False
            else:
                raise e

    def check_file_not_exists(self, path):
        """
        Check the file doesn't exist. Same as "not check_file_exists", just for convenience.

        :param path: the path to check
        :returns: True if the file doesn't exists, False otherwise
        """
        return not self.check_file_exists(path)

    def check_first_exists_second_not(self, path1, path2):
        """
        Check that path1 exists and path2 not.
        Same as "check_file_exists(path1) and check_file_not_exists(path2)", just for convenience

        :param path1: the path to check if it exists
        :param path2: the path to check if it doesn't exists
        :returns: True if path1 exists and path2 doesn't, False otherwise
        """
        return self.check_file_exists(path1) and self.check_file_not_exists(path2)

    def check_all_files_exists(self, *args):
        """
        Check that all files passed as params exists. Intended to be used with few files.

        :param args: files to be checked
        :returns: True if all files exist, False otherwise
        """
        gen = (self.check_file_exists(i) for i in args)
        return all(gen)

    def check_all_files_not_exists(self, *args):
        """
        Check that all files passed as params don't exists. Intended to be used with few files.

        :param args: files to be checked
        :returns: True if all files don't exist, False otherwise
        """
        gen = (self.check_file_not_exists(i) for i in args)
        return all(gen)

    def check_first_list_exists_second_list_not(self, pathlist1, pathlist2):
        """
        Check that all files in the first list exist and all files in the second list don't

        :param pathlist1: list of files that must exist
        :param pathlist2: list of files that mustn't exist
        :returns: True if all files in the first list exist and all files in the second
        list don't, False otherwise
        """
        return self.check_all_files_exists(*pathlist1) and self.check_all_files_not_exists(*pathlist2)

def pyocaction(username, password, async, method, *args, **kwargs):
    """
    Run an action using the pyocclient. This method will create an ownCloud client and run
    the method. A new client will be created each time.

    :param username: username for the client (for authentication purposes)
    :param password: password for the client (for authentication purposes)
    :param async: run the method async? True = async, False = sync
    :param method: the name of the method to be run from the owncloud client (check pyocclient
    Client object to know what methods you can use
    :param *args: arguments that will be passed to the method
    :param **kwargs: arguments that will be passed to the method. The extra keyword
    'pyocactiondebug' will enable debug in the Client object but won't be passed to the method

    :return: a tuple containing a Thread object and a Queue (to get the result of the called
    method once it finish) if the async param is set to True, and the result of the method
     if is set to False.

    examples:
    `pyocaction(user, pass, False, 'put_file_contents', '/path/to/file', 'file content')`
    `thread = pyocaction(user, pass, True, 'get_file', '/bigfile')`

    """
    oc_url = pyocclient_basic_url()
    if kwargs.get('pyocactiondebug'):
        client = owncloud.Client(oc_url, debug=True)
        del kwargs['pyocactiondebug']
    else:
        client = owncloud.Client(oc_url)
    client.login(username, password)

    caller = getattr(client, method)
    if async:

        def caller_wrapper(method, q, *args, **kwargs):
            q.put(method(*args, **kwargs))

        result_queue = Queue.Queue()
        caller_wrapper_args = (caller, result_queue,) + args
        thread = threading.Thread(target=caller_wrapper, args=caller_wrapper_args, kwargs=kwargs)
        thread.start()
        return (thread, result_queue)
    else:
        return caller(*args, **kwargs)

def pyocclient_basic_url():
    """
    Return the url to be used by pyocclient-related functions / classes
    """
    oc_protocol = 'https' if config.oc_ssl_enabled else 'http'
    oc_url = oc_protocol + '://' + config.oc_server + '/' + config.oc_root
    return oc_url
