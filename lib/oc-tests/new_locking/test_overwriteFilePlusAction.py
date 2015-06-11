import os
import tempfile
import owncloud
from smashbox.utilities import *
from smashbox.script import config as sconf

@add_worker
def overwriter(step):
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
    sum_orig = md5sum(target_filename)

    run_ocsync(d)
    list_files(d)

    step(2, 'overwrite file')

    tmpfile = tempfile.mkstemp()
    createfile(tmpfile[1], '5', count=1000, bs=10000)
    sum_new = md5sum(tmpfile[1])

    overwrite_thread = pyocaction(sconf.oc_account_name, sconf.oc_account_password, True, 'put_file', '/folder/bigfile.dat', tmpfile[1], pyocactiondebug=True)

    step(4, 'check result and cleanup')

    # wait until the download finish
    overwrite_thread[0].join()

    # download the file to check that it has been overwritten
    tmpfile2 = tempfile.mkstemp()
    get_file_result = pyocaction(sconf.oc_account_name, sconf.oc_account_password, False, 'get_file', '/folder/bigfile.dat', tmpfile2[1], pyocactiondebug=True)

    sum_downloaded = md5sum(tmpfile2[1])

    # check both md5 matches
    error_check(get_file_result, 'overwritten file failed to download')
    logger.debug('checking md5sum of the downloaded files')
    error_check(sum_orig != sum_new, 'original file didn\'t get ovewritten')
    error_check(sum_new == sum_downloaded, 'overwritten file is different than the downloaded file [%s] - [%s]' % (sum_new, sum_downloaded))

    # remove temporal files
    os.remove(tmpfile[1])
    os.remove(tmpfile2[1])

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

