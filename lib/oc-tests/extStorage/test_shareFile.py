
__doc__ = """

Test basic file sharing between users.  

+-----------+----------------------+------------------+----------------------------+
|  Step     |  Sharer              |  Sharee One      |  Sharee Two                |
|  Number   |                      |                  |                            |
+===========+======================+==================+============================|
|  2        | create work dir      | create work dir  |  create work dir           |
+-----------+----------------------+------------------+----------------------------+
|  3        | Create test files    |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  4        | Shares files with    |                  |                            |
|           | Sharee One           |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  5        |                      | Syncs and        |                            |
|           |                      | validates files  |                            |
+-----------+----------------------+------------------+----------------------------+
|  6        |                      | modifies one     |                            |
|           |                      | files, if        |                            |
|           |                      | permitted        |                            |
+-----------+----------------------+------------------+----------------------------+
|  7        | Validates modified   |                  |                            |
|           | file or not, based   |                  |                            |
|           | on permissions       |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  8        |                      | Shares a file    |                            |
|           |                      | with sharee two  |                            |
|           |                      | if permitted     |                            |
+-----------+----------------------+------------------+----------------------------+
|  9        |                      |                  |  Syncs and validates       |
|           |                      |                  |file is shared if permitted |
+-----------+----------------------+------------------+----------------------------+
|  10       | Sharer unshares a    |                  |                            |
|           | file                 |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  11       |                      | Syncs and        | Syncs and validates        |
|           |                      | validates file   | file not present           | 
|           |                      | not present      |                            |
+-----------+----------------------+------------------+----------------------------+
|  12       | Sharer deletes a     |                  |                            |
|           | file                 |                  |                            |
+-----------+----------------------+------------------+----------------------------+
|  13       |                      | Syncs and        |                            |
|           |                      | validates file   |                            |
|           |                      | not present      |                            |
+-----------+----------------------+------------------+----------------------------+
| 14        | Final step           | Final step       |        Final Step          |
+-----------+----------------------+------------------+----------------------------+


Data Providers:

  test_sharePermissions:      Permissions to be applied to the share

"""

from smashbox.utilities import *
import glob
import time
import MySQLdb

OCS_PERMISSION_READ = 1
OCS_PERMISSION_UPDATE = 2
OCS_PERMISSION_CREATE = 4
OCS_PERMISSION_DELETE = 8
OCS_PERMISSION_SHARE = 16
OCS_PERMISSION_ALL = 31

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
    reset_server_log_file()

    configure_storage () 
    add_storage_mount ('user1', 'amazon-s3')

    step (15, 'Validate server log file is clean') 
    d = make_workdir()
    scrape_log_file(d)

@add_worker
def sharer(step):

    step (2, 'Create workdir')
    d = make_workdir()

    step (3, 'Create initial test files and directories')

    createfile(os.path.join(d,'TEST_FILE_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_USER_RESHARE.dat'),'0',count=1000,bs=filesizeKB)
    createfile(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'),'0',count=1000,bs=filesizeKB)

    shared = reflection.getSharedObject()
    shared['md5_sharer'] = md5sum(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'))
    logger.info('md5_sharer: %s',shared['md5_sharer'])

    list_files(d)
    run_ocsync(d, user_num=1)
    list_files(d)

#    step (4,'Sharer shares files')

#    user1 = "%s%i"%(config.oc_account_name, 1)
#    user2 = "%s%i"%(config.oc_account_name, 2)

#    kwargs = {'perms': sharePermissions}
#    shared['TEST_FILE_USER_SHARE'] = share_file_with_user ('TEST_FILE_USER_SHARE.dat', user1, user2, **kwargs)
#    shared['TEST_FILE_USER_RESHARE'] = share_file_with_user ('TEST_FILE_USER_RESHARE.dat', user1, user2, **kwargs)
#    shared['TEST_FILE_MODIFIED_USER_SHARE'] = share_file_with_user ('TEST_FILE_MODIFIED_USER_SHARE.dat', user1, user2, **kwargs)
#    shared['sharer.TEST_FILE_MODIFIED_USER_SHARE'] = os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat')

#    step (7, 'Sharer validates modified file')
#    run_ocsync(d, user_num=1)

#    if not sharePermissions & OCS_PERMISSION_UPDATE:
#      expect_not_modified(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'), shared['md5_sharer'])
#    else:
#      expect_modified(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'), shared['md5_sharer'])

#    step (10, 'Sharer unshares a file')
#    delete_share (user1, shared['TEST_FILE_USER_RESHARE'])

#    step (12, 'Sharer deletes file')

#    list_files(d)
#    remove_file(os.path.join(d,'TEST_FILE_USER_SHARE.dat'))
#    run_ocsync(d, user_num=1)
#    list_files(d)

    step (14, 'Sharer final step')

#@add_worker
def shareeOne(step):

    step (2, 'Sharee One creates workdir')
    d = make_workdir()

    step (5, 'Sharee One syncs and validate files exist')

    run_ocsync(d, user_num=2)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_SHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    sharedFile = os.path.join(d,'TEST_FILE_USER_RESHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    sharedFile = os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat')
    logger.info ('Checking that %s is present in local directory for Sharee One', sharedFile)
    error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    step (6, 'Sharee One modifies TEST_FILE_MODIFIED_USER_SHARE.dat')

    modify_file(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'),'1',count=10,bs=filesizeKB)
    run_ocsync(d, user_num=2)
    list_files(d)

    shared = reflection.getSharedObject()
    if not sharePermissions & OCS_PERMISSION_UPDATE:
        # local file is modified, but not synced so the owner still has the right file
        list_files(d)
        expect_modified(os.path.join(d,'TEST_FILE_MODIFIED_USER_SHARE.dat'), shared['md5_sharer'])
        expect_not_modified(shared['sharer.TEST_FILE_MODIFIED_USER_SHARE'], shared['md5_sharer'])

    step (8, 'Sharee One share files with user 3')

    user2 = "%s%i"%(config.oc_account_name, 2)
    user3 = "%s%i"%(config.oc_account_name, 3)
    kwargs = {'perms': sharePermissions}
    result = share_file_with_user ('TEST_FILE_USER_RESHARE.dat', user2, user3, **kwargs)

    if not sharePermissions & OCS_PERMISSION_SHARE:
      error_check (result == -1, "shared and shouldn't have")

    step (11, 'Sharee one validates file does not exist after unsharing')

    run_ocsync(d, user_num=2)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_RESHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

    step (13, 'Sharee syncs and validates file does not exist')

    run_ocsync(d, user_num=2)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_SHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

    step (14, 'Sharee One final step')

#@add_worker
def shareeTwo(step):
  
    step (2, 'Sharee Two creates workdir')
    d = make_workdir()

    step (9, 'Sharee two validates share file')

    run_ocsync(d, user_num=3)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_RESHARE.dat')

    if not sharePermissions & OCS_PERMISSION_SHARE:
      logger.info ('Checking that %s is not present in local directory for Sharee Two', sharedFile)
      error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)
    else:
      logger.info ('Checking that %s is present in local directory for Sharee Two', sharedFile)
      error_check(os.path.exists(sharedFile), "File %s should exist" %sharedFile)

    step (11, 'Sharee two validates file does not exist after unsharing')

    run_ocsync(d, user_num=3)
    list_files(d)

    sharedFile = os.path.join(d,'TEST_FILE_USER_RESHARE.dat')
    logger.info ('Checking that %s is not present in sharee local directory', sharedFile)
    error_check(not os.path.exists(sharedFile), "File %s should not exist" %sharedFile)

    step (14, 'Sharee Two final step')


def configure_storage ():
    """ Update the database to support users creating their own external storage 
        mount points.  This is in place of an API and should be changed once the
        api and/or occ support is available"""

    db = None;
    db_schema = config.get('db_schema', 'owncloud')
    db_host = config.get ('db_host', '172.18.5.57')
    db_user = config.get ('db_user', 'root')
    db_password = config.get('db_password', 'Password01')

    try:

        db = MySQLdb.connect (db_host, db_user, db_password)
        cursor = db.cursor()

        cursor.execute ("select * from " + db_schema + ".appconfig where configkey = 'allow_user_mounting'")
        row_exists = cursor.fetchone()
        if row_exists is not None:
            cursor.execute ("delete from " +  db_schema + ".appconfig where configkey='allow_user_mounting';")

        cursor.execute ("select * from " + db_schema + ".appconfig where configkey = 'user_mounting_backends'")
        row_exists = cursor.fetchone()
        if row_exists is not None:
            cursor.execute ("delete from " +  db_schema + ".appconfig where configkey='user_mounting_backends';")

        cursor.execute ("insert into " +  db_schema + ".appconfig (appid, configkey, configvalue) values ('files_external', 'allow_user_mounting', 'yes');")

        cursor.execute ("insert into " +  db_schema + ".appconfig (appid, configkey, configvalue) values ('files_external', 'user_mounting_backends', '\\\OC\\\Files\\\Storage\\\AmazonS3');")

        db.commit()

    except Exception as e:

        print ("fatal error - need to handle this %s" %e)

    finally:

        if db is not None:
            db.close()


def add_storage_mount (user_name, mount_name):
    """ Create a mount.json file for the user and push it to the server
    """

    fn = open ('mount.json', 'w')
    fn.write ('{\n')
    fn.write ('    "user": {\n')
    fn.write ('        "' + user_name + '": {\n')
    fn.write ('            "\/' + user_name + '\/files\/' + mount_name + '": {\n')
    fn.write ('                "id": 1,\n')
    fn.write ('                "class": "\\\OC\\\Files\\\Storage\\\AmazonS3",\n')
    fn.write ('                "options": {\n')
    fn.write ('                    "key": "AKIAIEW7NKNGHC4A5LSA",\n')
    fn.write ('                    "secret": "riPbAV3Xx8y4K2V\/j\/iI8bFYGtEXo5HiY4I6jy+j",\n')
    fn.write ('                    "bucket": "owncloud-test-us-41",\n')
    fn.write ('                    "hostname": "",\n')
    fn.write ('                    "port": "",\n')
    fn.write ('                    "region": "",\n')
    fn.write ('                    "use_ssl": false,\n')
    fn.write ('                    "use_path_style": false\n')
    fn.write ('                 },\n')
    fn.write ('                 "storage_id": "4"\n')
    fn.write ('             }\n')
    fn.write ('         }\n')
    fn.write ('     }\n')
    fn.write ('}\n')

    fn.close()

#    cmd = 'scp -P %d mount.json root@%s:%s/%s/.' % (config.scp_port, config.oc_server, config.oc_server_datadirectory, user_name)
    cmd = 'rsync -a --chown=www-data:www-data --chmod=777 mount.json root@%s:%s/%s/.' % (config.oc_server, config.oc_server_datadirectory, user_name)
    rtn_code = runcmd(cmd)

    print cmd
    print 'returned %d' % rtn_code


