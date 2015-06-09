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
        },
        { 'action_method': 'move',
          'action_args': ('/folder/bigfile.dat', '/folder/bigrenamed.dat'),
          'action_kwargs': {'pyocactiondebug' : True},
          'extra_check': 'check_first_exists_second_not',
          'extra_check_params': ('/folder/bigrenamed.dat', '/folder/bigfile.dat')
        }
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
    createfile(target_filename,'10',count=1000,bs=10000)
    sum5 = md5sum(target_filename)

    run_ocsync(d)
    list_files(d)

    step(2, 'download file async')

    tmpfile = tempfile.mkstemp()
    # download the file asynchronously
    download_thread = pyocaction(sconf.oc_account_name, sconf.oc_account_password, True, 'get_file', '/folder/bigfile.dat', tmpfile[1], pyocactiondebug=True)

    step(3, 'wait and cleanup')

    # wait until the download finish
    download_thread[0].join()

    sum5_2 = md5sum(tmpfile[1])
    # check both md5 matches
    logger.info('checking md5sum of the downloaded files')
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
    result = pyocaction(sconf.oc_account_name, sconf.oc_account_password, False, method, *args, **kwargs)
    # check successful result
    logger.info('check %s method finished correctly' % method)
    error_check(result, method + ' action didn\'t finish correctly')

    # perform extra check
    check = config.get('extra_check', None)
    if check:
        logger.info('additional check %s' % check)
        check_params = config.get('extra_check_params', ())
        error_check(globals()[check](*check_params), 'extra check failed: %s %s' % (check, check_params))

