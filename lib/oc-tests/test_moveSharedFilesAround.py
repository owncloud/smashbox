
__doc__ = """

Test basic file sharing between users.  

+-----------+----------------------+------------------+----------------------------+
|  Step     |  user1               |  user2           |  Sharee Two                |
|  Number   |                      |                  |                            |
+===========+======================+==================+============================|
|  2        | create work dir      | create work dir  |  create work dir           |
+-----------+----------------------+------------------+----------------------------+
|  3        | Create test folder   |                  |                            |
|           |                      |                  |                            |
|           |                      |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  4        | Share test with      |                  |                            |
|           | user2                |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  5        |                      | Syncs and        |                            |
|           |                      | validates files  |                            |
+-----------+----------------------+------------------+----------------------------+
|  6        |                      | Create folder    |                            |
|           |                      | sub              |                            |
|           |                      |                  |                            |
|           |                      | Create several   |                            |
|           |                      | files            |                            |
|           |                      |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  7        |                      | Shares sub by    |                            |
|           |                      | link             |                            |
|           |                      |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  8        |                      | Move sub into    |                            |
|           |                      | test             |                            |
+-----------+----------------------+------------------+----------------------------+
|  9        | Syncs and validates  |                  |                            |
|           |                      |                  |                            | 
|           |                      |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  10       |                      |                  |      Check shared link     |
|           |                      |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  11       | Final step           | Final step       |        Final Step          |
+-----------+----------------------+------------------+----------------------------+


Data Providers:

  test_sharePermissions:      Permissions to be applied to the share

"""

from smashbox.utilities import *
import glob
import time

OCS_PERMISSION_READ = 1
OCS_PERMISSION_UPDATE = 2
OCS_PERMISSION_CREATE = 4
OCS_PERMISSION_DELETE = 8
OCS_PERMISSION_SHARE = 16
OCS_PERMISSION_ALL = 31

nfiles = 20

TEST_FILES = ['TEST_FILE_USER_SHARED_%02d.dat'%i for i in range(nfiles)]


filesizeKB = int(config.get('share_filesizeKB',10))
sharePermissions = config.get('test_sharePermissions', OCS_PERMISSION_ALL)

testsets = [
    { 
        'test_sharePermissions':OCS_PERMISSION_ALL
    },
    { 
        'test_sharePermissions':OCS_PERMISSION_READ | OCS_PERMISSION_UPDATE
    },
    { 
        'test_sharePermissions':OCS_PERMISSION_READ | OCS_PERMISSION_SHARE
    }
]

@add_worker
def setup(step):

    step (1, 'create test users')
    reset_owncloud_account(num_test_users=config.oc_number_test_users)
    check_users(config.oc_number_test_users)

    reset_rundir()

@add_worker
def user1_worker(step):

    step (2, 'Create workdir')
    d = make_workdir()

    step (3, 'Create initial test files and directories')

    test_folder = mkdir(os.path.join(d,'test'))

    shared = reflection.getSharedObject()
    #shared['md5_sharer'] = md5sum(os.path.join(d,'test'))
    #logger.info('md5_sharer: %s',shared['md5_sharer'])

    list_files(d)
    list_files(os.path.join(d,'test'))
    run_ocsync(d,user_num=1)
    list_files(d)

    step (4,'user1 shares files')

    user1 = "%s%i"%(config.oc_account_name, 1)
    user2 = "%s%i"%(config.oc_account_name, 2)

    kwargs = {'perms': sharePermissions}

    shared['TEST_FOLDER_USER_SHARE'] = share_file_with_user('test', user1, user2, **kwargs)


    step (11, 'user1 final step')

@add_worker
def user2_worker(step):

    step (2, 'user2 creates workdir')
    d = make_workdir()

    step (5, 'user2 syncs and validate files exist')

    run_ocsync(d,user_num=2)
    list_files(d)

    # for i in range(nfiles):
    #     sharedFile = os.path.join(os.path.join(d,test_folder),TEST_FILES[i])
    #     logger.info ('Checking that %s is present in local directory for user2', sharedFile)
    #     error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

 

    step (6, 'user2 creates folder sub and uploads test files into it')
    sub_folder = mkdir(os.path.join(d,'sub'))

    for i in range(nfiles):
        createfile(os.path.join(sub_folder,TEST_FILES[i]),'0',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    #shared['md5_sharer'] = md5sum(os.path.join(d,'sub'))
    #logger.info('md5_sharer: %s',shared['md5_sharer'])

    list_files(d)
    run_ocsync(d,user_num=2)
    list_files(d)

    step (7, 'user2 shares sub folder by link')

    user2 = "%s%i"%(config.oc_account_name, 2)
    #SHARING NOT SURE ABOUT THE WAY TO CALL THIS INSTRUCTION
    link_info = share_file_with_link('sub', user2)

    shared = reflection.getSharedObject()
    shared['link'] = link_info.link

    step (8, 'user2 moves folder sub into test folder')

    mv(sub_folder, os.path.join(d, 'test'))

    list_files(d)
    run_ocsync(d,user_num=2)
    list_files(d)

    step (11, 'user2 final step')



# def download_file(url, filename):

#     with open(filename, 'wb') as handle:
#         response = requests.get(url, stream=False)

#         if response.status_code == 200 :
#             for block in response.iter_content(1024):
#                 if not block:
#                     break

#                 handle.write(block) 

@add_worker
def user3_worker(step):
  
    step (10, 'user3 (external viewer) checks shared link')
    
    shared = reflection.getSharedObject()
    url = shared['link']
    download_file(url + '/download', config.smashdir + '/folder.zip') 

    returncode = runcmd('unzip ' + config.smashdir + '/folder.zip')

    logger.info('returncode of the unzip operation: %s', returncode)

    step (11, 'user3 (external viewer) final step')

