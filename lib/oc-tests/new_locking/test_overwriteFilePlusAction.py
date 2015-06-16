import os
import re
import tempfile
import uuid
import owncloud
from smashbox.utilities import *
from smashbox.script import config as sconf

def check_filesize(username, password, path, size):
    try:
        info = pyocaction(username, password, False, 'file_info', path)
        if info is None:
            return False
        else:
            return size == info.get_size()
    except owncloud.ResponseError as e:
        if e.status_code == 404:
            return False
        else:
            raise e

def parse_worker_number(worker_name):
    match = re.search(r'(\d+)$', worker_name)
    if match is not None:
        return int(match.group())
    else:
        return None

tmpname = tempfile.gettempdir() + os.sep + str(uuid.uuid4())

testsets = [
        { 'action_method': 'put_file_contents',
          'action_args': ('/folder/bigfile.dat', '123'*50),
          'action_kwargs': {'pyocactiondebug' : True},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_filesize',
          'extra_check_params': ('/folder/bigfile.dat', 3*50),
          'overwrite_kwargs' : {'chunked': False},
        },
#        { 'action_method': 'put_file_contents',
#          'action_args': ('/folder/bigfile.dat', '123'*50),
#          'action_kwargs': {'pyocactiondebug' : True},
#          'accounts': sconf.oc_number_test_users,
#          'extra_check': 'check_filesize',
#          'extra_check_params': ('/folder/bigfile.dat', 3*50),
#          'overwrite_kwargs' : {'chunked' : True, 'chunk_size' : 1024*1024}, #1MB
#        },
        { 'action_method': 'get_file',
          'action_args': ('/folder/bigfile.dat', tmpname),
          'action_kwargs': {'pyocactiondebug': True},
          'accounts': sconf.oc_number_test_users,
          'extra_check': 'check_filesize',  # check remotely
          'extra_check_params': ('/folder/bigfile.dat', 10000*1000),
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

    tmpfile = tempfile.mkstemp()
    createfile(tmpfile[1], '5', count=1000, bs=10000)
    sum_new = md5sum(tmpfile[1])

    overwrite_kwargs = {'pyocactiondebug' : True}
    if type(config.get('overwrite_kwargs', None)) is dict:
        overwrite_kwargs.update(config.get('overwrite_kwargs', None))
    overwrite_thread = pyocaction(user_account, sconf.oc_account_password, True, 'put_file', '/folder/bigfile.dat', tmpfile[1], **overwrite_kwargs)

    step(5, 'check result and cleanup')

    # wait until the download finish
    overwrite_thread[0].join()

    # download the file to check that it has been overwritten
    tmpfile2 = tempfile.mkstemp()
    get_file_result = pyocaction(user_account, sconf.oc_account_password, False, 'get_file', '/folder/bigfile.dat', tmpfile2[1], pyocactiondebug=True)

    sum_downloaded = md5sum(tmpfile2[1])

    # check both md5 matches
    error_check(get_file_result, 'overwritten file failed to download')
    logger.debug('checking md5sum of the downloaded files')
    error_check(sum_orig != sum_new, 'original file didn\'t get overwritten')
    error_check(sum_new == sum_downloaded, 'overwritten file is different than the downloaded file [%s] - [%s]' % (sum_new, sum_downloaded))

    # remove temporal files
    os.remove(tmpfile[1])
    os.remove(tmpfile2[1])

def doer(step):
    method = config.get('action_method', 'put_file_contents')
    args = config.get('action_args', ('/folder/bigfile.dat', '123'*50))
    kwargs = config.get('action_kwargs', {})

    process_number = parse_worker_number(reflection.getProcessName())
    user_account = sconf.oc_account_name if process_number <= 0 else '%s%i' % (sconf.oc_account_name, process_number)

    step(4, 'action over file')

    retry_action = False
    # perform the action
    try:
        result = pyocaction(user_account, sconf.oc_account_password, False, method, *args, **kwargs)
    except owncloud.ResponseError as e:
        logger.debug('%s action failed. Checking the status to know if the file is locked' % (method,))
        error_check(e.status_code == 423, 'unexpected status code [%i] : %s' % (e.status_code, e.get_resource_body()))
        retry_action = True

    step(6, 'check results')

    if retry_action:
        result = pyocaction(user_account, sconf.oc_account_password, False, method, *args, **kwargs)
    # check successful result
    error_check(result, method + ' action didn\'t finish correctly')

    # perform extra check
    check = config.get('extra_check', None)
    if check:
        logger.debug('additional check %s' % check)
        check_params = config.get('extra_check_params', ())
        error_check(globals()[check](user_account, sconf.oc_account_password, *check_params), 'extra check failed: %s %s' % (check, check_params))

# add workers
for i in range(1, config.get('accounts', 1) + 1):
    add_worker(overwriter, name='downloader_%s' % (i,))
    add_worker(doer, name='doer_%s' % (i,))
