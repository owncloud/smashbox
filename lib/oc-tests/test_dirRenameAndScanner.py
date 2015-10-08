__doc__ = """

This test renames a big folder ('mover' worked') to another name.
While the database is updating, another worker ('scanner' worker) will
try and trigger the scanner on its parent folder by doing a PROPFIND on it.
"""

# Number of test files in the subdirectory to rename
nfiles = int(config.get('dirRenameAndScanner_nfiles', 10))
# Number of renames to perform
renameiterations = int(config.get('dirRenameAndScanner_renameiterations', 10))
# Maximum time to way between scanner runs (random)
scanmaxdelay = int(config.get('dirRenameAndScanner_scanmaxdelay', 1.0))

from smashbox.utilities import *

testsets = [ 
    {'dirRenameAndScanner_nfiles': 100,
     'dirRenameAndScanner_renameiterations': 100,
     'dirRenameAndScanner_scanmaxdelay': 1.0
    },
]

import time
import tempfile


from smashbox.utilities.hash_files import *

@add_worker
def mover(step):
    step(1, 'init')
    d = make_workdir()

    reset_owncloud_account()
    reset_rundir()

    shared = reflection.getSharedObject()
    shared['finished'] = False
    
    step(2, 'upload test subdir')
    d2 = os.path.join(d, 'subdir')
    mkdir(d2)

    for i in range(nfiles):
        create_hashfile(d2, size=10)

    run_ocsync(d)

    step(4, 'rename the folder and sync')

    s1 = os.path.join(d, 'subdir')
    for i in range(renameiterations):
        logger.info('rename iteration %i', i)
        s2 = os.path.join(d, 'subdir-%i' % i)
        os.rename(s1, s2)
        s1 = s2;
        run_ocsync(d)

    shared['finished'] = True

    step(5, 'final check')
    run_ocsync(d)
    final_check(d)


@add_worker
def scanner(step):
    import random
    import time

    step(1, 'init')

    d = make_workdir()

    step(3, 'download the directory with the added files')
    d = make_workdir()
    run_ocsync(d)

    step(4, 'trigger propfind during rename')

    # sync continuously during rename
    shared = reflection.getSharedObject()
    while not shared['finished']:
        # arbitrary/random delay
        time.sleep(random.random() * scanmaxdelay)
        run_ocsync(d)

    step(5, 'final check')
    run_ocsync(d)
    final_check(d)

def final_check(d):

    list_files(d, recursive=True)

    d2 = os.path.join(d, 'subdir-%i' % (renameiterations - 1))
    
    logger.info('final output: %s', d2)

    all_files, analysed_files, bad_files = analyse_hashfiles(d2)

    error_check(bad_files == 0, '%s corrupted files in %s'%(bad_files,d2))
    error_check(analysed_files == nfiles, "not all files are present (%d/%d)"%(nfiles, analysed_files))

