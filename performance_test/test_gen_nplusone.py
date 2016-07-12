__doc__ = """ Add nfiles to a directory and check consistency.
The consistency will be checked by first, synchronising nfiles to the server from one sync-client (worker) process,
and the other sync-client process will be syncing down the added nfiles.
"""

from smashbox.utilities.hash_files import *
from smashbox.utilities.monitoring import push_to_monitoring, get_file_distr
import time

engine = config.get('engine',"owncloud")
if engine=="owncloud":
    from smashbox.utilities.ocengine import *
else:
    import sys
    print "Not supported sync engine [%s]! Exiting.."%engine
    sys.exit()

nfiles = int(config.get('nplusone_nfiles',10))
filesize = int(config.get('nplusone_filesize',1000))
syncid = int(time.time())
test_variable = get_file_distr(nfiles, filesize)
# optional fs check before files are uploaded by worker0
fscheck = config.get('nplusone_fscheck',False)

if type(filesize) is type(''):
    filesize = eval(filesize)

testsets = [
]

@add_worker
def worker0(step):
    setup_test()

    step(1,'Preparation')
    d = make_workdir()
    prepare_sync(d)
    run_sync(d)
    k0 = count_files(d)

    step(2,'Add %s files and check if we still have k1+nfiles after resync'%nfiles)

    total_size=0
    sizes=[]

    # compute the file sizes in the set
    for i in range(nfiles):
        size=size2nbytes(filesize)
        sizes.append(size)
        total_size+=size

    time0=time.time()
    logger.log(35,"Timestamp %f Files %d TotalSize %d",time.time(),nfiles,total_size)

    # create the test files
    for size in sizes:
        create_hashfile(d,size=size, bs=size)

    if fscheck:
        # drop the caches (must be running as root on Linux)
        try:
            runcmd('echo 3 > /proc/sys/vm/drop_caches')
        except Exception, e:
            logger.warn(e)
            logger.warn("Please run the script as root")
        
        ncorrupt = analyse_hashfiles(d)[2]
        fatal_check(ncorrupt==0, 'Corrupted files ON THE FILESYSTEM (%s) found'%ncorrupt)

    prepare_sync(d)
    time1=time.time()
    run_sync(d)
    time2 = time.time()

    ncorrupt = analyse_hashfiles(d)[2]
    
    k1 = count_files(d)

    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    fatal_check(ncorrupt==0, 'Corrupted files (%s) found'%ncorrupt)

    logger.info('SUCCESS: %d files found',k1)

    step(4,"Final report")

    if (k1-k0)==nfiles and ncorrupt==0:
        push_to_monitoring("upload_time",time2-time1,test_variable=test_variable,timestamp=syncid)
    push_to_monitoring("worker0synced_files",k1-k0,test_variable=test_variable,timestamp=syncid)

        
@add_worker
def worker1(step):
    step(1,'Preparation')
    d = make_workdir()
    prepare_sync(d)
    run_sync(d)
    k0 = count_files(d)

    step(3,'Resync and check files added by worker0')

    prepare_sync(d)
    time0=time.time()
    run_sync(d)
    time1 = time.time()

    ncorrupt = analyse_hashfiles(d)[2]
    k1 = count_files(d)

    if (k1-k0)==nfiles and ncorrupt==0:
        push_to_monitoring("download_time", time1-time0,test_variable=test_variable,timestamp=syncid)
    push_to_monitoring("cor", ncorrupt,test_variable=test_variable,timestamp=syncid)
    push_to_monitoring("worker1synced_files",k1-k0,test_variable=test_variable,timestamp=syncid)
                       
    error_check(k1-k0==nfiles,'Expecting to have %d files more: see k1=%d k0=%d'%(nfiles,k1,k0))

    fatal_check(ncorrupt==0, 'Corrupted files (%d) found'%ncorrupt) #Massimo 12-APR




