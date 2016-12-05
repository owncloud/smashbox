import os
import time

__doc__ = """
One files and shares uploader, one files downloader, one shares downloader. The share uploader creates and syncs (PROPFIND & PUT) nfiles. The files downloader syncs down the changes (PROPFIND & GET). After that, The share uploader shares the n files. At the end, share downloader sync down shared files.

+-----------+----------------------+------------------+----------------------------+
|  Step     |  Sharer              |  FilesReceiver   |  ShareReceiver             |
|  Number   |                      |                  |                            |
+===========+======================+==================+============================|
|  1        | create work dir      | create work dir  |  create work dir           |
+-----------+----------------------+------------------+----------------------------+
|  2        | Create test dir      |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  3        | Creates n files and  |                  |                            |
|           | syncs			       |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  4        |                      | Syncs files      |                            |
+-----------+----------------------+------------------+----------------------------+
|  5        | Shares n files       |                  |                            |
|           | with ShareReceiver   |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  6        | 			           |                  |  Syncs down the shared     |
|           |       		       |                  |  files                     |
+-----------+----------------------+------------------+----------------------------+
"""

OCS_PERMISSION_READ = 1
OCS_PERMISSION_UPDATE = 2
OCS_PERMISSION_CREATE = 4
OCS_PERMISSION_DELETE = 8
OCS_PERMISSION_SHARE = 16
OCS_PERMISSION_ALL = 31

# Files created by the uploader
nfiles = int(config.get('share_nfiles',3))
smashbox_steps_limit = int(config.get('smashbox_steps_limit',100))

filesize = config.get('share_filesize',1000)
fscheck = config.get('share_fscheck',True)
sharePermissions = config.get('test_sharePermissions', OCS_PERMISSION_ALL)
hash_filemask = 'hash_{md5}'

sharerNum = 1
shareReceiverNum = 2

from smashbox.utilities import *
from smashbox.utilities.hash_files import *

@add_worker
def setup(step):
    step(1, 'create test users')
    reset_owncloud_account(num_test_users=config.oc_number_test_users)
    check_users(config.oc_number_test_users)

    reset_rundir()

@add_worker
def sharer(step):
    step(2, 'Sharer preparation')
    d = make_workdir()
    run_ocsync(d,user_num=sharerNum)
    k0 = count_files(d)

    user1 = "%s%i"%(config.oc_account_name, sharerNum)
    user2 = "%s%i"%(config.oc_account_name, shareReceiverNum)
    shared = reflection.getSharedObject()
    kwargs = {'perms': sharePermissions}

    step(3, 'Add, sync and share %s files' % nfiles)

    files = []

    for i in range(nfiles):
        #STEP 1: create file on the filesystem
        fn = create_hashfile(d, size=filesize)
        if fscheck:
            ncorrupt = analyse_hashfiles(d)[2]
            fatal_check(ncorrupt == 0, 'Corrupted files ON THE FILESYSTEM (%s) found' % ncorrupt)

        files.append(os.path.basename(fn))

    step(4, 'Sync files (%i)' % nfiles)
    time0 = time.time()
    run_ocsync(d, user_num=sharerNum)
    time1 = time.time()

    step(6, 'Share files (%i)' % nfiles)

    for fileShare in files:
        #STEP 2: share file
        shared[str(i)] = share_file_with_user(fileShare, user1, user2, **kwargs)

    k1 = count_files(d)
    error_check(k1 - k0 == nfiles, 'Expecting to have %d files more: see k1=%d k0=%d' % (nfiles, k1, k0))

    step(7, 'Execute PROPFIND (sync of no changes) (%i)' % nfiles)
    time2 = time.time()
    run_ocsync(d, user_num=sharerNum)
    time3 = time.time()

    logger.info("SMASHED-SEND-SHARE-%i-%i=%f-%f" % (nfiles, filesize, time1 - time0, time3 - time2))

    k2 = count_files(d)
    ncorrupt = analyse_hashfiles(d)[2]
    error_check(k1 - k2 == 0, 'Expecting to have %d files more: see k1=%d k2=%d' % (nfiles, k1, k2))
    fatal_check(ncorrupt == 0, 'Corrupted files (%s) found' % ncorrupt)
    logger.info('SUCCESS: %d files found', k1)

    return

@add_worker
def sharerReceiver(step):

    step(2, 'Share receiver preparation')
    d = make_workdir()
    run_ocsync(d,user_num=shareReceiverNum)
    k0 = count_files(d)

    step(8, 'Share receiver will execute sync-down of shared % files' % nfiles)

    time0 = time.time()
    run_ocsync(d, user_num=shareReceiverNum)
    time1 = time.time()

    step(9, 'Share receiver will execute PROPFIND on shared % files' % nfiles)

    time2 = time.time()
    run_ocsync(d, user_num=shareReceiverNum)
    time3 = time.time()

    logger.info("SMASHED-RECV-SHARE-%i-%i=%f-%f" % (nfiles, filesize, time1 - time0, time3 - time2))

    ncorrupt = analyse_hashfiles(d)[2]
    k1 = count_files(d)

    error_check(k1 - k0 == nfiles, 'Expecting to have %d files more: see k1=%d k0=%d' % (nfiles, k1, k0))

    fatal_check(ncorrupt == 0, 'Corrupted files (%d) found' % ncorrupt)

    return

@add_worker
def filesReceiver(step):
    step(2, 'Files receiver preparation')
    d = make_workdir()

    #it will connect to the account of sharer and sync down the changes
    run_ocsync(d, user_num=sharerNum)
    k0 = count_files(d)

    step(5, 'Files receiver will execute sync-down of non-shared % files' % nfiles)

    time0 = time.time()

    #it will connect to the account of sharer and sync down the changes
    run_ocsync(d, user_num=sharerNum)
    time1 = time.time()

    step(10, 'Summarise')
    logger.info("SMASHED-RECV-FILES-%i-%i=%f" % (nfiles, filesize, time1 - time0))

    ncorrupt = analyse_hashfiles(d)[2]
    k1 = count_files(d)

    error_check(k1 - k0 == nfiles, 'Expecting to have %d files more: see k1=%d k0=%d' % (nfiles, k1, k0))

    fatal_check(ncorrupt == 0, 'Corrupted files (%d) found' % ncorrupt)

    return