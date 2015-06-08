import time
import os
import tempfile
from multiprocessing import Semaphore
from smashbox.utilities import *
from smashbox.script import config as sconf


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
    createfile(target_filename,'10',count=1000,bs=25000)
    sum5 = md5sum(target_filename)

    run_ocsync(d)
    list_files(d)

    step(2, 'download file')

    tmpfile = tempfile.mkstemp()
    #download the file asynchronously
    download_thread = pyocaction(sconf.oc_account_name, sconf.oc_account_password, True, 'get_file', '/folder/bigfile.dat', tmpfile[1], pyocactiondebug=True)

    step(3, 'cleanup')

    #wait until the download finish
    download_thread[0].join()
    logger.info('finished')
    sum5_2 = md5sum(tmpfile[1])

    error_check(sum5 == sum5_2, 'uploaded file is different than the downloaded file [%s] - [%s]' % (sum5, sum5_2))
    os.remove(tmpfile[1])

@add_worker
def deleter(step):
    step(3, 'delete file')
    result = pyocaction(sconf.oc_account_name, sconf.oc_account_password, False, 'put_file_contents', '/folder/bigfile.dat', '123'*50, pyocactiondebug=True)
    error_check(result, 'put_file_content action didn\'t finish correctly')
    logger.info('finished')
