import owncloud
import threading
import Queue

class pyocclient_wrapper(object):
    def __init__(self, url, username=None, password=None, **kwargs):
        client = owncloud.Client(url, **kwargs)
        if username != None and password != None:
            client.login(username, password)
        self._client = client

    def do_action(self, method, *args, **kwargs):
        caller = getattr(self._client, method)
        return caller(*args, **kwargs)

    def do_action_async(self, method, *args, **kwargs):
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
        try:
            info = self.do_action('file_info', path)
            return False if info is None else size == info.get_size()
        except owncloud.ResponseError as e:
            if e.status_code == 404:
                return False
            else:
                raise e

    def check_file_exists(self, path):
        try:
            info = self.do_action('file_info', path)
            return False if info is None else True
        except owncloud.ResponseError as e:
            if e.status_code == 404:
                return False
            else:
                raise e

    def check_file_not_exists(self, path):
        return not self.check_file_exists(path)

    def check_first_exists_second_not(self, path1, path2):
        return self.check_file_exists(path1) and self.check_file_not_exists(path2)

    def check_all_files_exists(self, *args):
        gen = (self.check_file_exists(i) for i in args)
        return all(gen)

    def check_all_files_not_exists(self, *args):
        gen = (self.check_file_not_exists(i) for i in args)
        return all(gen)

    def check_first_list_exists_second_list_not(self, pathlist1, pathlist2):
        return self.check_all_files_exists(*pathlist1) and self.check_all_files_not_exists(*pathlist2)
