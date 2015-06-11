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
| 1           | upload big file           |                |
+-------------+---------------------------+----------------+
| 2           | download big file (async) |                |
+-------------+---------------------------+----------------+
| 3           |                           | perform action |
+-------------+---------------------------+----------------+
| 4           | check result and cleanup  | check result   |
+-------------+---------------------------+----------------+

"""
import time
import os
import tempfile
import owncloud
from smashbox.utilities import *
from smashbox.script import config as sconf

def check_file_exists(path):
    try:
        info = pyocaction(sconf.oc_account_name, sconf.oc_account_password, False, 'file_info', path)
        return False if info is None else True
    except owncloud.ResponseError as e:
        if e.status_code == 404:
            return False
        else:
            raise e

def check_file_not_exists(path):
    return not check_file_exists(path)

def check_filesize(path, size):
    try:
        info = pyocaction(sconf.oc_account_name, sconf.oc_account_password, False, 'file_info', path)
        if info is None:
            return False
        else:
            return size == info.get_size()
    except owncloud.ResponseError as e:
        if e.status_code == 404:
            return False
        else:
            raise e

def check_first_exists_second_not(path1, path2):
    return check_file_exists(path1) and check_file_not_exists(path2)

def check_all_files_not_exists(*args):
    gen = (check_file_not_exists(i) for i in args)
    return all(gen)

def check_all_files_exists(*args):
    gen = (check_file_exists(i) for i in args)
    return all(gen)

def check_first_list_exists_second_list_not(pathlist1, pathlist2):
    return check_all_files_exists(*pathlist1) and check_all_files_not_exists(*pathlist2)

testsets = [
        { 'action_method': 'put_file_contents',
          'action_args': ('/folder/bigfile.dat', '123'*50),
          'action_kwargs': {'pyocactiondebug' : True},
          'extra_check': 'check_filesize',
          'extra_check_params': ('/folder/bigfile.dat', 3*50)
        },
        { 'action_method': 'delete',
          'action_args': ('/folder/bigfile.dat',),
          'action_kwargs': {'pyocactiondebug' : True},
          'extra_check': 'check_file_not_exists',
          'extra_check_params': ('/folder/bigfile.dat',)
        },
        { 'action_method': 'file_info',
          'action_args': ('/folder/bigfile.dat',),
          'action_kwargs': {'pyocactiondebug' : True},
          'extra_check': None,
          'extra_check_params': ()
        },
        { 'action_method': 'move',
          'action_args': ('/folder/bigfile.dat', '/folder/bigrenamed.dat'),
          'action_kwargs': {'pyocactiondebug' : True},
          'extra_check': 'check_first_exists_second_not',
          'extra_check_params': ('/folder/bigrenamed.dat', '/folder/bigfile.dat')
        },
        { 'action_method': 'move',
          'action_args': ('/folder/bigfile.dat', '/folder2/bigfile.dat'),
          'action_kwargs': {'pyocactiondebug' : True},
          'extra_check': 'check_first_exists_second_not',
          'extra_check_params': ('/folder2/bigfile.dat', '/folder/bigfile.dat')
        },
        { 'action_method': 'delete',
          'action_args': ('/folder',),
          'action_kwargs': {'pyocactiondebug' : True},
          'extra_check': 'check_all_files_not_exists',
          'extra_check_params': ('/folder/bigfile.dat', '/folder')
        },
        { 'action_method': 'move',
          'action_args': ('/folder', '/folder-renamed'),
          'action_kwargs': {'pyocactiondebug' : True},
          'extra_check': 'check_first_list_exists_second_list_not',
          'extra_check_params': (('/folder-renamed', '/folder-renamed/bigfile.dat'),
                                    ('/folder', '/folder/bigfile.dat'))
        },
        { 'action_method': 'move',
          'action_args': ('/folder', '/folder2/folder'),
          'action_kwargs': {'pyocactiondebug' : True},
          'extra_check': 'check_first_list_exists_second_list_not',
          'extra_check_params': (('/folder2', '/folder2/folder', '/folder2/folder/bigfile.dat'),
                                    ('/folder', '/folder/bigfile.dat'))
        },
]

@add_worker
def downloader(step):
    reset_owncloud_account()
    reset_rundir()

    step(1, 'create big file')

    d = make_workdir()

    list_files(d)
    run_ocsync(d)

    # sync a big file
    target_filename = os.path.join(d, 'folder', 'bigfile.dat')
    mkdir(os.path.join(d, 'folder'))
    mkdir(os.path.join(d, 'folder2'))
    createfile(target_filename,'10',count=1000,bs=10000)
    sum5 = md5sum(target_filename)

    run_ocsync(d)
    list_files(d)

    step(2, 'download file async')

    tmpfile = tempfile.mkstemp()
    # download the file asynchronously
    download_thread = pyocaction(sconf.oc_account_name, sconf.oc_account_password, True, 'get_file', '/folder/bigfile.dat', tmpfile[1], pyocactiondebug=True)

    step(4, 'check result and cleanup')

    # wait until the download finish
    download_thread[0].join()

    sum5_2 = md5sum(tmpfile[1])
    # check both md5 matches
    logger.debug('checking md5sum of the downloaded files')
    error_check(sum5 == sum5_2, 'uploaded file is different than the downloaded file [%s] - [%s]' % (sum5, sum5_2))
    # remove temporal file
    os.remove(tmpfile[1])

@add_worker
def doer(step):
    method = config.get('action_method', 'put_file_contents')
    args = config.get('action_args', ('/folder/bigfile.dat', '123'*50))
    kwargs = config.get('action_kwargs', {})

    step(3, 'action over file')

    # perform the action
    try:
        result = pyocaction(sconf.oc_account_name, sconf.oc_account_password, False, method, *args, **kwargs)

        step(4, 'check results')
        # check successful result
        logger.debug('check %s method finished correctly' % method)
        error_check(result, method + ' action didn\'t finish correctly')

        # perform extra check
        check = config.get('extra_check', None)
        if check:
            logger.debug('additional check %s' % check)
            check_params = config.get('extra_check_params', ())
            error_check(globals()[check](*check_params), 'extra check failed: %s %s' % (check, check_params))
    except owncloud.ResponseError as e:
        logger.debug('%s action failed. Checking the status to know if the file is locked' % (method,))
        error_check(e.status_code == 423, 'unexpected status code [%i] : %s' % (e.status_code, e.get_resource_body()))


