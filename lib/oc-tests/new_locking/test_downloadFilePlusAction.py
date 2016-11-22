__doc__ = """
Test locking feature. The test will download a file big enough and perform an operation
while the download is running. Each test set will run a different operation.

Test sets:
* download + overwrite
* download + delete
* download + info (propfind)
* download + rename
* download + move
* download + delete parent folder
* download + rename folder
* download + move folder

+-------------+---------------------------+----------------+
| step number | downloader                | doer           |
+-------------+---------------------------+----------------+
| 2           | upload big file           |                |
+-------------+---------------------------+----------------+
| 3           | download big file (async) |                |
+-------------+---------------------------+----------------+
| 4           |                           | perform action |
+-------------+---------------------------+----------------+
| 5           | check result and cleanup  | check result   |
+-------------+---------------------------+----------------+

"""
import time
import os
import re
import tempfile
import owncloud
import smashbox.utilities.pyocclient_wrapper
from smashbox.utilities import *
from smashbox.script import config as sconf

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
          'extra_check_params': ('/folder/bigfile.dat', 3*50)
        },
        { 'action_method': 'delete',
          'action_args': ('/folder/bigfile.dat',),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_file_not_exists',
          'extra_check_params': ('/folder/bigfile.dat',)
        },
        { 'action_method': 'file_info',
          'action_args': ('/folder/bigfile.dat',),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': None,
          'extra_check_params': ()
        },
        { 'action_method': 'move',
          'action_args': ('/folder/bigfile.dat', '/folder/bigrenamed.dat'),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_first_exists_second_not',
          'extra_check_params': ('/folder/bigrenamed.dat', '/folder/bigfile.dat')
        },
        { 'action_method': 'move',
          'action_args': ('/folder/bigfile.dat', '/folder2/bigfile.dat'),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_first_exists_second_not',
          'extra_check_params': ('/folder2/bigfile.dat', '/folder/bigfile.dat')
        },
        { 'action_method': 'delete',
          'action_args': ('/folder',),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_all_files_not_exists',
          'extra_check_params': ('/folder/bigfile.dat', '/folder')
        },
        { 'action_method': 'move',
          'action_args': ('/folder', '/folder-renamed'),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_first_list_exists_second_list_not',
          'extra_check_params': (('/folder-renamed', '/folder-renamed/bigfile.dat'),
                                    ('/folder', '/folder/bigfile.dat'))
        },
        { 'action_method': 'move',
          'action_args': ('/folder', '/folder2/folder'),
          'action_kwargs': {},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_first_list_exists_second_list_not',
          'extra_check_params': (('/folder2', '/folder2/folder', '/folder2/folder/bigfile.dat'),
                                    ('/folder', '/folder/bigfile.dat'))
        },
]

@add_worker
def setup(step):
    step(1, 'setup')
    reset_owncloud_account(num_test_users=config.get('accounts', 1))
    reset_rundir()

def downloader(step):
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
    sum5 = md5sum(target_filename)

    run_ocsync(d, user_num=None if process_number <= 0 else process_number)
    list_files(d)

    step(3, 'download file async')

    try:
        tmpfile = tempfile.mkstemp()
        # download the file asynchronously
        download_thread = client_wrapper.do_action_async('get_file', '/folder/bigfile.dat', tmpfile[1])

        step(5, 'check result and cleanup')

        # wait until the download finish
        download_thread[0].join()
        download_result = download_thread[1].get()
        if isinstance(download_result, Exception):
            raise download_result
        else:
            error_check(download_result, 'download file failed')

        sum5_2 = md5sum(tmpfile[1])
        # check both md5 matches
        logger.debug('checking md5sum of the downloaded files')
        error_check(sum5 == sum5_2, 'uploaded file is different than the downloaded file [%s] - [%s]' % (sum5, sum5_2))
    finally:
        # remove temporal file
        os.remove(tmpfile[1])

def doer(step):
    method = config.get('action_method', 'put_file_contents')
    args = config.get('action_args', ('/folder/bigfile.dat', '123'*50))
    kwargs = config.get('action_kwargs', {})

    process_number = parse_worker_number(reflection.getProcessName())
    user_account = sconf.oc_account_name if process_number <= 0 else '%s%i' % (sconf.oc_account_name, process_number)

    step(2, 'synced setup')

    client_wrapper = pyocclient_wrapper.pyocclient_wrapper(pyocclient_wrapper.pyocclient_basic_url(), user_account, sconf.oc_account_password, debug=True)

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
    logger.debug('check %s method finished correctly' % method)
    error_check(result, method + ' action didn\'t finish correctly')

    # perform extra check
    check = config.get('extra_check', None)
    if check:
        logger.debug('additional check %s' % check)
        check_params = config.get('extra_check_params', ())
        error_check(getattr(client_wrapper, check)(*check_params), 'extra check failed: %s %s' % (check, check_params))

# add workers
for i in range(1, config.get('accounts', 1) + 1):
    add_worker(downloader, name='downloader_%s' % (i,))
    add_worker(doer, name='doer_%s' % (i,))
