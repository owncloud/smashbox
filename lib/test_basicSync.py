__doc__ = """ Test basic sync and conflbfnicts: files are modified and deleted by one or both workers (winner and loser); optionally remove local state db on one of the clients (loser).

There are four clients (workers):

 - creator - populates the directory initially and also performs a final check
 - winner  - is syncing its local changes first
 - loser   - is syncing its local changes second (and optionally it looses the local sync database before doing the sync)
 - checker - only performs a final check (without having interacted with the system before)

Note: in 1.6 client conflict files are excluded by default - so they should be never propagated to the server
Note: in 1.5 the exclusion list should be provided separately to the client (FIXME)

Note on effects of removing local state db (1.6):

 - any files modified remotely or locally get a conflict if both remote and local replicas exist (FIXME: this could be possibly more refined in the future based on timestamps or content checksums)
 - any files not present locally but present remotely will be downloaded (so a deletion won't be propagated)

"""

from smashbox.utilities import * 

import glob
import time

filesizeKB = int(config.get('basicSync_filesizeKB',10000))

# True => remove local sync db on the loser 
# False => keep the loser 
rmLocalStateDB = bool(config.get('basicSync_rmLocalStateDB',False))

# True => use new webdav endpoint (dav/files)
# False => use old webdav endpoint (webdav)
use_new_dav_endpoint = bool(config.get('use_new_dav_endpoint',True))

testsets = [
        { 'basicSync_filesizeKB': 1000,
          'basicSync_rmLocalStateDB':False,
          'use_new_dav_endpoint':True
        },
        { 'basicSync_filesizeKB': 1000,
          'basicSync_rmLocalStateDB':False,
          'use_new_dav_endpoint':False
        },
        { 'basicSync_filesizeKB': 50000, 
          'basicSync_rmLocalStateDB':False,
          'use_new_dav_endpoint':True
        },
        { 'basicSync_filesizeKB': 50000,
          'basicSync_rmLocalStateDB':False,
          'use_new_dav_endpoint':False
        },
        { 'basicSync_filesizeKB': 1000,
          'basicSync_rmLocalStateDB':True,
          'use_new_dav_endpoint':True
        },
        { 'basicSync_filesizeKB': 1000,
          'basicSync_rmLocalStateDB':True,
          'use_new_dav_endpoint':False
        },
        { 'basicSync_filesizeKB': 50000, 
          'basicSync_rmLocalStateDB':True,
          'use_new_dav_endpoint':True
        },
        { 'basicSync_filesizeKB': 50000,
          'basicSync_rmLocalStateDB':True,
          'use_new_dav_endpoint':False
        }
]

def expect_content(fn,md5):
    actual_md5 = md5sum(fn)
    error_check(actual_md5 == md5, "inconsistent md5 of %s: expected %s, got %s"%(fn,md5,actual_md5))

def expect_no_deleted_files(d):
    expect_deleted_files(d,[])

def expect_deleted_files(d,expected_deleted_files):
    actual_deleted_files = glob.glob(os.path.join(d,'*_DELETED*'))
    logger.debug('deleted files in %s: %s',d,actual_deleted_files)

    error_check(len(expected_deleted_files) == len(actual_deleted_files), "expected %d got %d deleted files"%(len(expected_deleted_files),len(actual_deleted_files)))

    for fn in expected_deleted_files:
        error_check(any([fn in dfn for dfn in actual_deleted_files]), "expected deleted file for %s not found"%fn)
 

def expect_conflict_files(d,expected_conflict_files):
    actual_conflict_files = get_conflict_files(d)

    logger.debug('conflict files in %s: %s',d,actual_conflict_files)

    error_check(len(expected_conflict_files) == len(actual_conflict_files), "expected %d got %d conflict files"%(len(expected_conflict_files),len(actual_conflict_files)))

    exp_basefns = [os.path.splitext(fn)[0] for fn in expected_conflict_files]

    logger.debug(exp_basefns)
    logger.debug(actual_conflict_files)

    for bfn in exp_basefns:
        error_check(any([bfn in fn for fn in actual_conflict_files]), "expected conflict file for %s not found"%bfn)
    
def expect_no_conflict_files(d):
    expect_conflict_files(d,[])

def final_check(d,shared):
    """ This is the final check applicable to all workers - this reflects the status of the remote repository so everyone should be in sync.
    The only potential differences are with locally generated conflict files.
    """

    list_files(d)
    expect_content(os.path.join(d,'TEST_FILE_MODIFIED_NONE.dat'), shared['md5_creator'])

    expect_content(os.path.join(d,'TEST_FILE_ADDED_LOSER.dat'), shared['md5_loser'])

    if not rmLocalStateDB:
        expect_content(os.path.join(d,'TEST_FILE_MODIFIED_LOSER.dat'), shared['md5_loser'])
    else:
        expect_content(os.path.join(d,'TEST_FILE_MODIFIED_LOSER.dat'), shared['md5_creator']) # in this case, a conflict is created on the loser and file on the server stays the same

    expect_content(os.path.join(d,'TEST_FILE_ADDED_WINNER.dat'), shared['md5_winner'])
    expect_content(os.path.join(d,'TEST_FILE_MODIFIED_WINNER.dat'), shared['md5_winner'])
    expect_content(os.path.join(d,'TEST_FILE_ADDED_BOTH.dat'), shared['md5_winner'])     # a conflict on the loser, server not changed
    expect_content(os.path.join(d,'TEST_FILE_MODIFIED_BOTH.dat'), shared['md5_winner'])  # a conflict on the loser, server not changed

    if not rmLocalStateDB:
        expect_no_deleted_files(d) # normally any deleted files should not come back
    else:
        expect_deleted_files(d, ['TEST_FILE_DELETED_LOSER.dat', 'TEST_FILE_DELETED_WINNER.dat']) # but not TEST_FILE_DELETED_BOTH.dat !
        expect_content(os.path.join(d,'TEST_FILE_DELETED_LOSER.dat'), shared['md5_creator']) # this file should be downloaded by the loser because it has no other choice (no previous state to compare with)
        expect_content(os.path.join(d,'TEST_FILE_DELETED_WINNER.dat'), shared['md5_creator']) # this file should be re-uploaded by the loser because it has no other choice (no previous state to compare with)

def finish_if_not_capable():
    # Finish the test if some of the prerequisites for this test are not satisfied
    if compare_oc_version('10.0', '<') and use_new_dav_endpoint == True:
        #Dont test for <= 9.1 with new endpoint, since it is not supported
        logger.warn("Skipping test since webdav endpoint is not capable for this server version")
        return True
    if compare_client_version('3.0', '>=') and use_new_dav_endpoint == False:
        # Don't test for client version >= 3.0 with old endpoint, since it is not supported
        logger.warn("Skipping test since old webdav endpoint is not support for this client version")
        return True
    return False
    
@add_worker
def creator(step):
    if finish_if_not_capable():
        return

    reset_owncloud_account()
    reset_rundir()

    step(1,'create initial content and sync')

    d = make_workdir()

    # files *_NONE are not modified by anyone after initial sync
    # files *_LOSER are modified by the loser but not by the winner
    # files *_WINNER are modified by the winner but not by the loser
    # files *_BOTH are modified both by the winner and by the loser (always conflict on the loser)

    createfile(os.path.join(d,'TEST_FILE_MODIFIED_NONE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_LOSER.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_WINNER.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_BOTH.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_DELETED_LOSER.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_DELETED_WINNER.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_DELETED_BOTH.dat'),'0',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_creator'] = md5sum(os.path.join(d,'TEST_FILE_MODIFIED_NONE.dat'))
    logger.info('md5_creator: %s',shared['md5_creator'])

    list_files(d)
    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)
    list_files(d)

    time.sleep(1)

    step(7,'download the repository')

    run_ocsync(d,n=3, use_new_dav_endpoint=use_new_dav_endpoint)

    time.sleep(1)

    step(8,'final check')

    final_check(d,shared)
    expect_no_conflict_files(d) 

@add_worker
def winner(step):
    if finish_if_not_capable():
        return

    step(2,'initial sync')

    d = make_workdir()
    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    step(3,'modify locally and sync to server')

    list_files(d)

    remove_file(os.path.join(d,'TEST_FILE_DELETED_WINNER.dat'))
    remove_file(os.path.join(d,'TEST_FILE_DELETED_BOTH.dat'))

    createfile(os.path.join(d,'TEST_FILE_MODIFIED_WINNER.dat'),'1',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_BOTH.dat'),'1',count=1000,bs=filesizeKB)

    createfile(os.path.join(d,'TEST_FILE_ADDED_WINNER.dat'),'1',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_ADDED_BOTH.dat'),'1',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_winner'] = md5sum(os.path.join(d,'TEST_FILE_ADDED_WINNER.dat'))
    logger.info('md5_winner: %s',shared['md5_winner'])

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    time.sleep(1)

    step(5,'final sync')

    run_ocsync(d,n=3, use_new_dav_endpoint=use_new_dav_endpoint)

    time.sleep(1)

    step(8,'final check')

    final_check(d,shared)
    expect_no_conflict_files(d) 


# this is the loser which lost it's local state db after initial sync

@add_worker
def loser(step):
    if finish_if_not_capable():
        return

    step(2,'initial sync')

    d = make_workdir()
    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    step(4,'modify locally and sync to the server')

    list_files(d)

    # now do the local changes

    remove_file(os.path.join(d,'TEST_FILE_DELETED_LOSER.dat'))
    remove_file(os.path.join(d,'TEST_FILE_DELETED_BOTH.dat'))

    createfile(os.path.join(d,'TEST_FILE_MODIFIED_LOSER.dat'),'2',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_BOTH.dat'),'2',count=1000,bs=filesizeKB)

    createfile(os.path.join(d,'TEST_FILE_ADDED_LOSER.dat'),'2',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_ADDED_BOTH.dat'),'2',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_loser'] = md5sum(os.path.join(d,'TEST_FILE_ADDED_LOSER.dat'))
    logger.info('md5_loser: %s',shared['md5_loser'])


    #os.system('curl -v -s -k -XPROPFIND --data @/b/eos/CURL-TEST/p2.dat %s| xmllint --format -'%oc_webdav_url(remote_folder='TEST_FILE_MODIFIED_BOTH.dat'))
    #os.system('sqlite3 -line /tmp/smashdir/test_basicSync/loser/.csync_journal.db  \'select * from metadata where path like "%TEST_FILE_MODIFIED_BOTH%"\'')

    # remove the sync db
    if rmLocalStateDB:
        remove_db_in_folder(d)

    run_ocsync(d,n=3, use_new_dav_endpoint=use_new_dav_endpoint) # conflict file will be synced to the server but it requires more than one sync run

    time.sleep(1)

    step(6,'final sync')

    run_ocsync(d, use_new_dav_endpoint=use_new_dav_endpoint)

    time.sleep(1)

    step(8,'final check')

    #os.system('sqlite3 -line /tmp/smashdir/test_basicSync/loser/.csync_journal.db  \'select * from metadata where path like "%TEST_FILE_MODIFIED_BOTH%"\'')

    final_check(d,shared)
    if not rmLocalStateDB:
        expect_conflict_files(d, ['TEST_FILE_ADDED_BOTH.dat', 'TEST_FILE_MODIFIED_BOTH.dat' ])
    else:
        expect_conflict_files(d, ['TEST_FILE_ADDED_BOTH.dat', 'TEST_FILE_MODIFIED_BOTH.dat', 
                                  'TEST_FILE_MODIFIED_LOSER.dat', 'TEST_FILE_MODIFIED_WINNER.dat']) # because the local and remote state is different and it is assumed that this is a conflict (FIXME: in the future timestamp-based last-restort check could improve this situation)

@add_worker
def checker(step):
    if finish_if_not_capable():
        return

    shared = reflection.getSharedObject()

    step(7,'download the repository for final verification')
    d = make_workdir()
    
    run_ocsync(d,n=3, use_new_dav_endpoint=use_new_dav_endpoint)

    time.sleep(1)

    step(8,'final check')

    final_check(d,shared)
    expect_no_conflict_files(d)