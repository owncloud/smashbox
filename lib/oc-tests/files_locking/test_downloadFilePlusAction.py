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

testsets = [
        { 'action_method': 'put_file_contents',
          'action_args': ('/folder/bigfile.dat', '123'*50),
          'action_kwargs': {'pyocactiondebug' : True}
        },
        { 'action_method': 'delete',
          'action_args': ('/folder/bigfile.dat',),
          'action_kwargs': {'pyocactiondebug' : True},
          'extra_check': 'check_file_not_exists',
          'extra_check_params': ('/folder/bigfile.dat',)
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

    target_filename = os.path.join(d, 'folder', 'bigfile.dat')
    mkdir(os.path.join(d, 'folder'))
    createfile(target_filename,'10',count=1000,bs=10000)
    sum5 = md5sum(target_filename)

    run_ocsync(d)
    list_files(d)

    step(2, 'download file async')

    tmpfile = tempfile.mkstemp()
    #download the file asynchronously
    download_thread = pyocaction(sconf.oc_account_name, sconf.oc_account_password, True, 'get_file', '/folder/bigfile.dat', tmpfile[1], pyocactiondebug=True)

    step(3, 'wait and cleanup')

    #wait until the download finish
    download_thread[0].join()
    logger.info('finished')
    sum5_2 = md5sum(tmpfile[1])

    error_check(sum5 == sum5_2, 'uploaded file is different than the downloaded file [%s] - [%s]' % (sum5, sum5_2))
    os.remove(tmpfile[1])

@add_worker
def doer(step):
    method = config.get('action_method', 'put_file_contents')
    args = config.get('action_args', ('/folder/bigfile.dat', '123'*50))
    kwargs = config.get('action_kwargs', {})

    step(3, 'action over file')

    result = pyocaction(sconf.oc_account_name, sconf.oc_account_password, False, method, *args, **kwargs)
    error_check(result, method + ' action didn\'t finish correctly')

    check = config.get('extra_check', None)
    if check:
        check_params = config.get('extra_check_params', ())
        error_check(globals()[check](*check_params), 'extra check failed: %s %s' % (check, check_params))
    logger.info('finished')
