
__doc__ = """

Test uploading a large number of files to a directory and then syncing

+-----------+----------------------+------------------+----------------------------+
|  Step     |  Sharer              |  Sharee One      |  Sharee Two                |
|  Number   |                      |                  |                            |
+===========+======================+==================+============================|
|  2        | create work dir      | create work dir  |  create work dir           |
+-----------+----------------------+------------------+----------------------------+
|  3        | Create test dir      |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  4        | Shares test dir with |                  |                            |
|           | Sharee One and Two   |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  5        |                      | Syncs shared dir | syncs Shared dir           |
+-----------+----------------------+------------------+----------------------------+
|  6        |                      | creates new      |                            |
|           |                      | files and syncs  |                            |
+-----------+----------------------+------------------+----------------------------+
|  7        | syncs and validates  |                  |  syncs and validates       |
|           | new files exist      |                  |  new files exist           |
+-----------+----------------------+------------------+----------------------------+
|  8        | final step           | final step       |  final step                |
+-----------+----------------------+------------------+----------------------------+

Data Providers:

  test_sharePermissions:      Permissions to be applied to the share
  test_numFilesToCreate:      Number of files to create
  test_filesizeKB:            Size of file to create in KB
  share_sets:                 Number of sharer/shareeOne/shareeTwo groupings to be
                              used in a test run


"""

from smashbox.utilities import *
import glob
import re

OCS_PERMISSION_READ = 1
OCS_PERMISSION_UPDATE = 2
OCS_PERMISSION_CREATE = 4
OCS_PERMISSION_DELETE = 8
OCS_PERMISSION_SHARE = 16
OCS_PERMISSION_ALL = 31

filesizeKB = int(config.get('test_filesizeKB',10))
sharePermissions = int(config.get('test_sharePermissions', OCS_PERMISSION_ALL))
numFilesToCreate = int(config.get('test_numFilesToCreate', 10))
share_sets = int(config.get('share_sets',1))

testsets = [
    {
        'test_sharePermissions':OCS_PERMISSION_ALL,
        'test_numFilesToCreate':50,
        'test_filesizeKB':20000,
        'share_sets': 1,
    },
    {
        'test_sharePermissions':OCS_PERMISSION_ALL,
        'test_numFilesToCreate':500,
        'test_filesizeKB':2000,
        'share_sets': 1,
    },
    {
        'test_sharePermissions':OCS_PERMISSION_READ | OCS_PERMISSION_CREATE | OCS_PERMISSION_UPDATE,
        'test_numFilesToCreate':50,
        'test_filesizeKB':20000,
        'share_sets': 1,
    },
]

@add_worker
def setup(step):

    step (1, 'create test users')
    num_users = 3 * share_sets
    print ('creating %d users' % num_users)
    reset_owncloud_account(num_test_users=num_users)
    check_users(num_users)

    reset_rundir()
    reset_server_log_file()

    step (9, 'Validate server log file is clean')

    d = make_workdir()
    scrape_log_file(d)


def sharer(step):

    step (2,'Create workdir')
    d = make_workdir()
    sharer_num = get_user_number_from_work_directory(d)

    step (3,'Create initial test directory')

    mkdir(os.path.join(d, 'localShareDir'))
    max_user_num = sharer_num * 3

    list_files(d)
    run_ocsync(d,user_num=max_user_num-2)
    list_files(d)

    step (4,'Sharer shares directory')

    user1 = "%s%i"%(config.oc_account_name, max_user_num-2)
    user2 = "%s%i"%(config.oc_account_name, max_user_num-1)
    user3 = "%s%i"%(config.oc_account_name, max_user_num)

    shared = reflection.getSharedObject()

    kwargs = {'perms': sharePermissions}
    index1 = "%s%i"%('SHARE_LOCAL_DIR_U2_', sharer_num)
    index2 = "%s%i"%('SHARE_LOCAL_DIR_U3_', sharer_num)
    shared[index1] = share_file_with_user ('localShareDir', user1, user2, **kwargs)
    shared[index2] = share_file_with_user ('localShareDir', user1, user3, **kwargs)

    step (7, 'Sharer validates newly added files')

    run_ocsync(d,user_num=max_user_num-2)

    list_files(os.path.join(d,'localShareDir'))
    checkFilesExist(d, max_user_num-2)

    step (8, 'Sharer final step')

for i in range(share_sets):
    add_worker (sharer,name="sharer%02d"%(i+1))

def shareeOne(step):

    step (2, 'Sharee One creates workdir')
    d = make_workdir()
    shareeOne_num = get_user_number_from_work_directory(d)
    max_user_num = shareeOne_num * 3

    step (5,'Sharee One syncs and validates directory exist')

    run_ocsync(d,user_num=max_user_num-1)
    list_files(d)

    sharedDir = os.path.join(d,'localShareDir')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedDir)
    error_check(os.path.exists(sharedDir), "Directory %s should exist" %sharedDir)

    step (6, 'Sharee One creates files')

    logger.info ('ShareeOne is creating %i files', numFilesToCreate)
    if numFilesToCreate == 1:
      createfile(os.path.join(d,'localShareDir', 'TEST_FILE_NEW_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    else:
      for i in range(1, numFilesToCreate):
        filename = "%s%i%s" % ('TEST_FILE_NEW_USER_SHARE_',i,'.dat')
        createfile(os.path.join(d,'localShareDir', filename),'0',count=1000,bs=filesizeKB)

    run_ocsync(d,user_num=max_user_num-1)
    username = "%s%i" % (config.oc_account_name, max_user_num-1)

    if numFilesToCreate == 1:
      expect_server_file_exists(username, os.path.join('localShareDir', 'TEST_FILE_NEW_USER_SHARE.dat'))
    else:
      for i in range(1, numFilesToCreate):
        filename = "%s%i%s" % ('TEST_FILE_NEW_USER_SHARE_',i,'.dat')
        expect_server_file_exists(username, os.path.join('localShareDir', filename))

    list_files(os.path.join(d,'localShareDir'))
    checkFilesExist(d, max_user_num-1)

    step (8, 'Sharee One final step')

for i in range(share_sets):
    add_worker (shareeOne,name="shareeOne%02d"%(i+1))

def shareeTwo(step):
  
    step (2, 'Sharee Two creates workdir')
    d = make_workdir()
    shareeTwo_num = get_user_number_from_work_directory(d)
    max_user_num = shareeTwo_num * 3

    sharedDir = mkdir(os.path.join(d, 'localShareDir'))

    step (5, 'Sharee two syncs and validates directory exists')

    username = "%s%i" % (config.oc_account_name, max_user_num)
    expect_server_file_exists(username, 'localShareDir', isDir=True)

    run_ocsync(d,user_num=max_user_num)
    list_files(d)

    logger.info ('Checking that %s is present in local directory for Sharee One', sharedDir)
    expect_exists(sharedDir, isDir=True)

    step (7, 'Sharee two validates new files exist')

    run_ocsync(d,user_num=max_user_num)

    list_files(sharedDir)
    checkFilesExist(d, max_user_num)

    step (8, 'Sharee Two final step')

for i in range(share_sets):
    add_worker (shareeTwo,name="shareeTwo%02d"%(i+1))

def checkFilesExist (tmpDir, user_num):

    logger.info ('Checking if files exist in local directory ')
    username = "%s%i" % (config.oc_account_name, user_num)

    if numFilesToCreate == 1:
        sharedFile = os.path.join(tmpDir,'localShareDir', 'TEST_FILE_NEW_USER_SHARE.dat')
        logger.info ('Checking that %s is present in local directory ', sharedFile)
        expect_exists(sharedFile)
        expect_server_file_exists(username,os.path.join('localShareDir', 'TEST_FILE_NEW_USER_SHARE.dat'))
    else:
      for i in range(1,numFilesToCreate):
        filename = "%s%i%s" % ('TEST_FILE_NEW_USER_SHARE_',i,'.dat')
        logger.info ('Checking that %s is present in local directory ', filename)
        sharedFile = os.path.join(tmpDir, 'localShareDir', filename)
        expect_exists(sharedFile)
        expect_server_file_exists(username,os.path.join('localShareDir', filename))


def get_user_number_from_work_directory(dir):
    """
    :param dir: string Path of the directory
        /home/user/smashdir/test_uploadFiles-150522-111229/shareeTwo01
    :return: integer User number from the last directory name
    """

    # Remove the config.rundir from the path before searching for the integer
    # dir = /home/user/smashdir/test_uploadFiles-150522-111229/shareeTwo01
    dir = dir[len(config.rundir) + 1:]

    # dir = shareeTwo01
    user_num = int(re.search(r'\d+', dir).group())

    # user_num = 1
    return user_num
