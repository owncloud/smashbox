import os
import time

__doc__ = """
One share uploader, one share downloader. The share uploader creates, syncs (PROPFIND & PUT) and shares nfiles. The share downloader, after nth share uploader sequence, syncs down the changes (PROPFIND & GET)

For each Nth file, following steps will be executed:
#STEP 1: Sharer: create file on the filesystem
#STEP 2: Sharer: sync file (PROPFIND and PUT)
#STEP 3: Sharer: share file
#STEP 4: Sharer: Log the execution in following format: Filename - Number of files - Filesize - PROPFIND&PUT duration - SHARE duration
#STEP 5: ShareReceiver: Sync down the change introduced by sharer
#STEP 6: ShareReceiver:  Log the execution in following format: Number of files - Filesize - PROPFIND&GET duration

cat oc-stable-9-0/log-test_nSharedFiles.log | grep SYNC-SHARE | grep -oP '5-1000=\K.*'
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
required_steps = 2*nfiles+7

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
    if required_steps > smashbox_steps_limit:
        fatal_check(required_steps <= smashbox_steps_limit, 'Cannot execute test which requires (%i) found, but only (%i) are configured. '
                                                       'Please use [-o smashbox_steps_limit=N] flag to increase number of steps to required one' % (required_steps, smashbox_steps_limit))
    step(1, 'create test users')
    reset_owncloud_account(num_test_users=config.oc_number_test_users)
    check_users(config.oc_number_test_users)

    reset_rundir()

@add_worker
def sharer(step):
    if required_steps > smashbox_steps_limit:
        return
    step(2, 'Sharer preparation')
    d = make_workdir()
    run_ocsync(d,user_num=sharerNum)
    k0 = count_files(d)

    user1 = "%s%i"%(config.oc_account_name, sharerNum)
    user2 = "%s%i"%(config.oc_account_name, shareReceiverNum)
    shared = reflection.getSharedObject()
    kwargs = {'perms': sharePermissions}

    step(3, 'Add, sync and share %s files' % nfiles)

    next_step = 4;
    for i in range(nfiles):
        #STEP 1: create file on the filesystem
        fn = create_hashfile(d, size=filesize)
        if fscheck:
            ncorrupt = analyse_hashfiles(d)[2]
            fatal_check(ncorrupt == 0, 'Corrupted files ON THE FILESYSTEM (%s) found' % ncorrupt)

        #STEP 2: sync file (PROPFIND and PUT) and measure the time
        time0 = time.time()
        run_ocsync(d, user_num=sharerNum)

        time1 = time.time()

        #STEP 3: share file and measure the time
        fileShare = os.path.basename(fn)
        shared[str(i)] = share_file_with_user(fileShare, user1, user2, **kwargs)

        time2 = time.time()

        #STEP 4: Log the execution in following format:
        # Filename - Number of files - Filesize - PROPFIND&PUT duration - SHARE duration
        logger.info("SMASHED-SYNC-SHARE-%s-%i-%i=%f-%f" % (fileShare, nfiles, filesize, time1 - time0, time2 - time1))
        next_step = next_step + 2
        step(next_step, 'Synced and shared file %s' % i)

    next_step = next_step + 2
    step(next_step, 'Sharer - check correctness')

    ncorrupt = analyse_hashfiles(d)[2]
    k1 = count_files(d)

    error_check(k1 - k0 == nfiles, 'Expecting to have %d files more: see k1=%d k0=%d' % (nfiles, k1, k0))
    fatal_check(ncorrupt == 0, 'Corrupted files (%s) found' % ncorrupt)
    logger.info('SUCCESS: %d files found', k1)

    return


@add_worker
def sharerReceiver(step):
    if required_steps > smashbox_steps_limit:
        return

    step(2, 'Share receiver preparation')
    d = make_workdir()
    run_ocsync(d,user_num=shareReceiverNum)
    k0 = count_files(d)

    next_step = 5;
    step(next_step, 'Share receiver will execute sync for each of % files' % nfiles)

    for i in range(nfiles):
        #STEP 1: sync down the shared file (PROPFIND and GET) and measure the time
        time0 = time.time()
        run_ocsync(d,user_num=shareReceiverNum)
        time1 = time.time()
        logger.info("SMASHED-RECEIVER-%i-%i=%f" % (nfiles, filesize, time1 - time0))
        next_step = next_step + 2
        step(next_step, 'Synced down %s' % i)

    next_step = next_step + 2
    step(next_step, 'ShareReceiver - check correctness')

    ncorrupt = analyse_hashfiles(d)[2]
    k1 = count_files(d)

    error_check(k1 - k0 == nfiles, 'Expecting to have %d files more: see k1=%d k0=%d' % (nfiles, k1, k0))

    fatal_check(ncorrupt == 0, 'Corrupted files (%d) found' % ncorrupt)

    return
