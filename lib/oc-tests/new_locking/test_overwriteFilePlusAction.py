__doc__ = """
Test locking feature. The test will ovewrite a file big enough and perform an operation
while the overwrite is running. Each test set will run a different operation.
Chunked uploads are currently outside of the tests

Test sets:
* overwrite + overwrite
* overwrite + download file
* overwrite + info (propfind)
* overwrite + download folder as zip
* overwrite + delete file
* overwrite + delete folder
* overwrite + rename file
* overwrite + move file
* overwrite + rename folder
* overwrite + move folder

+-------------+----------------------------+--------------------+
| step number | overwriter                 | doer               |
+-------------+----------------------------+--------------------+
| 2           | upload big file            | create working dir |
+-------------+----------------------------+--------------------+
| 3           | overwrite big file (async) |                    |
+-------------+----------------------------+--------------------+
| 4           |                            | perform action     |
+-------------+----------------------------+--------------------+
| 5           | check result and cleanup   |                    |
+-------------+----------------------------+--------------------+
| 6           |                            | check result       |
+-------------+----------------------------+--------------------+
"""

import os
import re
import tempfile
import uuid
import owncloud
import zipfile
import smashbox.utilities.pyocclient_wrapper
from smashbox.utilities import *
from smashbox.script import config as sconf

def check_local_filesize(localpath, size):
    '''username and password remains to keep the expected signature'''
    return os.path.getsize(localpath) == size

def check_zip_contents(localpath, content_list):
    checked_result = False
    with zipfile.ZipFile(localpath, 'r') as myzip:
        checked_result = myzip.namelist() == content_list
    return checked_result

def parse_worker_number(worker_name):
    match = re.search(r'(\d+)$', worker_name)
    if match is not None:
        return int(match.group())
    else:
        return None


testsets = [
        { 'action_method': 'put_file_contents',
          'action_args': ('/folder/bigfile.dat', '123'*50),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_filesize',
          'extra_check_params': ('/folder/bigfile.dat', 3*50),
          'overwrite_kwargs' : {'chunked': False},
        },
#  chunked uploads aren't supported for the moment
#        { 'action_method': 'put_file_contents',
#          'action_args': ('/folder/bigfile.dat', '123'*50),
#          'action_kwargs': {'pyocactiondebug' : True},
#          'accounts': sconf.oc_number_test_users,
#          'extra_check': 'check_filesize',
#          'extra_check_params': ('/folder/bigfile.dat', 3*50),
#          'overwrite_kwargs' : {'chunked' : True, 'chunk_size' : 1024*1024}, #1MB
#        },
        { 'action_method': 'get_file',
          'action_args': ['/folder/bigfile.dat', 'bigfile.dat'],
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_local_filesize',
          'extra_check_params': ['bigfile.dat', 10000*1000],
          'overwrite_kwargs' : {'chunked': False},
        },
        { 'action_method': 'file_info',
          'action_args': ('/folder/bigfile.dat',),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': None,
          'extra_check_params': (),
          'overwrite_kwargs' : {'chunked': False},
        },
#  currently failing due to https://github.com/owncloud/core/issues/16960
#        { 'action_method': 'get_directory_as_zip',
#          'action_args': ['/folder', 'folder.zip'],
#          'action_kwargs': {},
#          'accounts': sconf.oc_number_test_users,
#          'extra_check': 'check_zip_contents',
#          'extra_check_params': ['folder.zip', ['folder/', 'folder/bigfile.dat']],
#          'overwrite_kwargs' : {'chunked': False},
#        },
        { 'action_method': 'delete',
          'action_args': ('/folder/bigfile.dat',),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_file_not_exists',
          'extra_check_params': ('/folder/bigfile.dat',),
          'overwrite_kwargs' : {'chunked': False},
        },
        { 'action_method': 'delete',
          'action_args': ('/folder',),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_all_files_not_exists',
          'extra_check_params': ('/folder/bigfile.dat', '/folder'),
          'overwrite_kwargs' : {'chunked': False},
        },
        { 'action_method': 'move',
          'action_args': ('/folder/bigfile.dat', '/folder/bigrenamed.dat'),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_first_exists_second_not',
          'extra_check_params': ('/folder/bigrenamed.dat', '/folder/bigfile.dat'),
          'overwrite_kwargs' : {'chunked': False},
        },
        { 'action_method': 'move',
          'action_args': ('/folder/bigfile.dat', '/folder2/bigfile.dat'),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_first_exists_second_not',
          'extra_check_params': ('/folder2/bigfile.dat', '/folder/bigfile.dat'),
          'overwrite_kwargs' : {'chunked': False},
        },
        { 'action_method': 'move',
          'action_args': ('/folder', '/folder-renamed'),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_first_list_exists_second_list_not',
          'extra_check_params': (('/folder-renamed', '/folder-renamed/bigfile.dat'),
                                    ('/folder', '/folder/bigfile.dat')),
          'overwrite_kwargs' : {'chunked': False},
        },
        { 'action_method': 'move',
          'action_args': ('/folder', '/folder2/folder'),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_first_list_exists_second_list_not',
          'extra_check_params': (('/folder2', '/folder2/folder', '/folder2/folder/bigfile.dat'),
                                    ('/folder', '/folder/bigfile.dat')),
          'overwrite_kwargs' : {'chunked': False},
        },
]

@add_worker
def setup(step):
    step(1, 'setup')
    reset_owncloud_account(num_test_users=config.get('accounts', 1))
    reset_rundir()

def overwriter(step):
    process_number = parse_worker_number(reflection.getProcessName())
    user_account = sconf.oc_account_name if process_number <= 0 else '%s%i' % (sconf.oc_account_name, process_number)

    step(2, 'create big file')

    client_wrapper = pyocclient_wrapper.pyocclient_wrapper(pyocclient_wrapper.pyocclient_basic_url(), user_account, sconf.oc_account_password, debug=True)

    d = make_workdir()

    list_files(d)
    run_ocsync(d, user_num=None if process_number <= 0 else process_number)

    # sync a big file
    target_filename = os.path.join(d, 'folder', 'bigfile.dat')
    mkdir(os.path.join(d, 'folder'))
    mkdir(os.path.join(d, 'folder2'))
    createfile(target_filename,'10',count=1000,bs=10000)
    sum_orig = md5sum(target_filename)

    run_ocsync(d, user_num=None if process_number <= 0 else process_number)
    list_files(d)


    step(3, 'overwrite file')

    try:
        tmpfile = tempfile.mkstemp()
        createfile(tmpfile[1], '5', count=1000, bs=10000)
        sum_new = md5sum(tmpfile[1])

        overwrite_kwargs = config.get('overwrite_kwargs', {})
        overwrite_thread = client_wrapper.do_action_async('put_file', '/folder/bigfile.dat', tmpfile[1], **overwrite_kwargs)

        step(5, 'check result and cleanup')

        # wait until the overwrite finish
        overwrite_thread[0].join()
        overwrite_result = overwrite_thread[1].get()
        if isinstance(overwrite_result, Exception):
            raise overwrite_result
        else:
            error_check(overwrite_result, 'put file failed')

        # download the file to check that it has been overwritten
        tmpfile2 = tempfile.mkstemp()
        get_file_result = client_wrapper.do_action('get_file', '/folder/bigfile.dat', tmpfile2[1])

        sum_downloaded = md5sum(tmpfile2[1])

        # check both md5 matches
        error_check(get_file_result, 'overwritten file failed to download')
        logger.debug('checking md5sum of the downloaded files')
        error_check(sum_orig != sum_new, 'original file didn\'t get overwritten')
        error_check(sum_new == sum_downloaded, 'overwritten file is different than the downloaded file [%s] - [%s]' % (sum_new, sum_downloaded))
    finally:
        # remove temporal files
        for tfile in ('tmpfile', 'tmpfile2'):
            if tfile in locals():
                os.remove(locals()[tfile][1])

def doer(step):
    method = config.get('action_method', 'put_file_contents')
    args = config.get('action_args', ('/folder/bigfile.dat', '123'*50))
    kwargs = config.get('action_kwargs', {})

    process_number = parse_worker_number(reflection.getProcessName())
    user_account = sconf.oc_account_name if process_number <= 0 else '%s%i' % (sconf.oc_account_name, process_number)

    step(2, 'create working dir in case it\'s needed')

    client_wrapper = pyocclient_wrapper.pyocclient_wrapper(pyocclient_wrapper.pyocclient_basic_url(), user_account, sconf.oc_account_password, debug=True)

    d = make_workdir()

    if method in ('get_file', 'get_directory_as_zip'):
        # we need to cheat at this two method to make them work properly
        args[1] = os.path.join(d, args[1])

    step(4, 'action over file')

    retry_action = False
    # perform the action
    try:
        result = client_wrapper.do_action(method, *args, **kwargs)
    except owncloud.ResponseError as e:
        logger.debug('%s action failed. Checking the status to know if the file is locked' % (method,))
        error_check(e.status_code == 423, 'unexpected status code [%i] : %s' % (e.status_code, e.get_resource_body()))
        retry_action = True

    step(6, 'check results')

    if retry_action:
        result = client_wrapper.do_action(method, *args, **kwargs)
    # check successful result
    error_check(result, method + ' action didn\'t finish correctly')

    # perform extra check
    check = config.get('extra_check', None)
    if check:
        logger.debug('additional check %s' % check)
        check_params = config.get('extra_check_params', ())
        if method in ('get_file', 'get_directory_as_zip'):
            # we need to cheat at this two method to make them work properly
            check_params[0] = os.path.join(d, check_params[0])
            error_check(globals()[check](*check_params), 'extra check failed: %s %s' % (check, check_params))
        else:
            error_check(getattr(client_wrapper, check)(*check_params), 'extra check failed: %s %s' % (check, check_params))

# add workers
for i in range(1, config.get('accounts', 1) + 1):
    add_worker(overwriter, name='overwriter_%s' % (i,))
    add_worker(doer, name='doer_%s' % (i,))
