
__doc__ = """

Test share permission enforcement

+-----------+----------------------+------------------------+
|  Step     | Owner                |  Recipient             |
|  Number   |                      |                        |
+===========+======================+========================+
|  2        | Create work dir      | Create work dir        |
+-----------+----------------------+------------------------+
|  3        | Create test folder   |                        |
+-----------+----------------------+------------------------+
|  4        | Shares folder with   |                        |
|           | Recipient            |                        |
+-----------+----------------------+------------------------+
|  5        |                      | Check permission       |
|           |                      | enforcement for every  |
|           |                      | operation              |
+-----------+----------------------+------------------------+
|  6        | Final                | Final                  |
+-----------+----------------------+------------------------+

Data Providers:

  sharePermissions_matrix: Permissions to be applied to the share,
                                combined with the expected result for
                                every file operation

"""

from smashbox.utilities import *

import owncloud

OCS_PERMISSION_READ = 1
OCS_PERMISSION_UPDATE = 2
OCS_PERMISSION_CREATE = 4
OCS_PERMISSION_DELETE = 8
OCS_PERMISSION_SHARE = 16
OCS_PERMISSION_ALL = 31

ALL_OPERATIONS = [
    # a new file can be uploaded/created (file target does not exist)
    'upload',
    # a file can overwrite an existing one
    'upload_overwrite',
    # rename file to new name, all within the shared folder
    'rename',
    # move a file from outside the shared folder into the shared folder
    'move_in',
    # move a file from outside the shared folder and overwrite a file inside the shared folder
    # (note: SabreDAV automatically deletes the target file first before moving, so requires DELETE permission too)
    'move_in_overwrite',
    # move a file already in the shared folder into a subdir within the shared folder
    'move_in_subdir',
    # move a file already in the shared folder into a subdir within the shared folder and overwrite an existing file there
    'move_in_subdir_overwrite',
    # move a file to outside of the shared folder
    'move_out',
    # move a file out of a subdir of the shared folder into the shared folder
    'move_out_subdir',
    # delete a file inside the shared folder
    'delete',
    # create folder inside the shared folder
    'mkdir',
    # delete folder inside the shared folder
    'rmdir',
]

"""
    Permission matrix parameters (they all default to False):

    - 'permission': permissions to apply
    - 'allowed_operations': allowed operations, see ALL_OPERATIONS for more info
"""
testsets = [{ 
        'sharePermissions_matrix': {
            'permission': OCS_PERMISSION_ALL,
            'allowed_operations': [
                'upload',
                'upload_overwrite',
                'rename',
                'move_in',
                'move_in_overwrite',
                'move_in_subdir',
                'move_in_subdir_overwrite',
                'move_out',
                'move_out_subdir',
                'delete',
                'mkdir',
                'rmdir',
            ]
        }
    }, { 
        'sharePermissions_matrix': {
            'permission': OCS_PERMISSION_READ,
            'allowed_operations': []
        }
    }, { 
        'sharePermissions_matrix': {
            'permission': OCS_PERMISSION_READ | OCS_PERMISSION_CREATE,
            'allowed_operations': [
                'upload',
                'move_in',
                'mkdir',
            ]
        }
    }, {
        'sharePermissions_matrix': {
            'permission': OCS_PERMISSION_READ | OCS_PERMISSION_UPDATE,
            'allowed_operations': [
                'upload_overwrite',
                'rename',
            ]
        }
    }, {
        'sharePermissions_matrix': {
            'permission': OCS_PERMISSION_READ | OCS_PERMISSION_DELETE,
            'allowed_operations': [
                'move_out',
                'delete',
                'rmdir',
            ]
        }
    }, {
        'sharePermissions_matrix': {
            'permission': OCS_PERMISSION_READ | OCS_PERMISSION_CREATE | OCS_PERMISSION_UPDATE,
            'allowed_operations': [
                'upload',
                'upload_overwrite',
                'rename',
                'move_in',
                'mkdir',
            ]
        }
    }, {
        'sharePermissions_matrix': {
            'permission': OCS_PERMISSION_READ | OCS_PERMISSION_CREATE | OCS_PERMISSION_DELETE,
            'allowed_operations': [
                'upload',
                'move_in',
                'move_in_overwrite',
                'move_in_subdir',
                'move_in_subdir_overwrite',
                'move_out',
                'move_out_subdir',
                'delete',
                'mkdir',
                'rmdir',
            ]
        }
    }, {
        'sharePermissions_matrix': {
            'permission': OCS_PERMISSION_READ | OCS_PERMISSION_UPDATE | OCS_PERMISSION_DELETE,
            'allowed_operations': [
                'upload_overwrite',
                'rename',
                'move_out',
                'delete',
                'rmdir',
            ]
        }
    }
]

permission_matrix = config.get('sharePermissions_matrix', testsets[0]['sharePermissions_matrix'])

SHARED_DIR_NAME = 'shared-dir'

@add_worker
def setup(step):

    step (1, 'create test users')
    reset_owncloud_account(num_test_users=2)
    check_users(2)

    reset_rundir()

@add_worker
def owner_worker(step):

    step (2, 'Create workdir')
    d = make_workdir()

    step (3, 'Create test folder')

    logger.info(permission_matrix)
    perms = permission_matrix['permission']

    mkdir(os.path.join(d, SHARED_DIR_NAME))
    mkdir(os.path.join(d, SHARED_DIR_NAME, 'subdir'))

    mkdir(os.path.join(d, SHARED_DIR_NAME, 'delete_this_dir'))
    createfile(os.path.join(d, SHARED_DIR_NAME, 'move_this_out.dat'),'0',count=1000,bs=1)
    createfile(os.path.join(d, SHARED_DIR_NAME, 'move_this_to_subdir.dat'),'0',count=1000,bs=1)
    createfile(os.path.join(d, SHARED_DIR_NAME, 'move_this_to_subdir_for_overwrite.dat'),'0',count=1000,bs=1)
    createfile(os.path.join(d, SHARED_DIR_NAME, 'subdir', 'move_this_out.dat'),'0',count=1000,bs=1)
    createfile(os.path.join(d, SHARED_DIR_NAME, 'subdir', 'overwrite_this.dat'),'0',count=1000,bs=1)
    createfile(os.path.join(d, SHARED_DIR_NAME, 'rename_this.dat'),'0',count=1000,bs=1)
    createfile(os.path.join(d, SHARED_DIR_NAME, 'overwrite_this.dat'),'0',count=1000,bs=1)
    createfile(os.path.join(d, SHARED_DIR_NAME, 'overwrite_this_through_move_in.dat'),'0',count=1000,bs=1)
    createfile(os.path.join(d, SHARED_DIR_NAME, 'delete_this.dat'),'0',count=1000,bs=1)

    createfile(os.path.join(d, SHARED_DIR_NAME, 'delete_this_dir', 'stuff.dat'),'0',count=1000,bs=1)

    list_files(d)
    run_ocsync(d, user_num=1)
    list_files(d)
    user1 = "%s%i"%(config.oc_account_name, 1)

    expect_server_file_exists(user1, os.path.join(SHARED_DIR_NAME, 'subdir'))
    expect_server_file_exists(user1, os.path.join(SHARED_DIR_NAME, 'delete_this_dir'))
    expect_server_file_exists(user1, os.path.join(SHARED_DIR_NAME, 'move_this_out.dat'))
    expect_server_file_exists(user1, os.path.join(SHARED_DIR_NAME, 'move_this_to_subdir.dat'))
    expect_server_file_exists(user1, os.path.join(SHARED_DIR_NAME, 'move_this_to_subdir_for_overwrite.dat'))
    expect_server_file_exists(user1, os.path.join(SHARED_DIR_NAME, 'subdir', 'move_this_out.dat'))
    expect_server_file_exists(user1, os.path.join(SHARED_DIR_NAME, 'subdir', 'overwrite_this.dat'))
    expect_server_file_exists(user1, os.path.join(SHARED_DIR_NAME, 'rename_this.dat'))
    expect_server_file_exists(user1, os.path.join(SHARED_DIR_NAME, 'overwrite_this.dat'))
    expect_server_file_exists(user1, os.path.join(SHARED_DIR_NAME, 'overwrite_this_through_move_in.dat'))
    expect_server_file_exists(user1, os.path.join(SHARED_DIR_NAME, 'delete_this.dat'))
    expect_server_file_exists(user1, os.path.join(SHARED_DIR_NAME, 'delete_this_dir', 'stuff.dat'))

    step (4, 'Shares folder with recipient')

    user1 = "%s%i"%(config.oc_account_name, 1)
    user2 = "%s%i"%(config.oc_account_name, 2)
    kwargs = {'perms': perms}
    share_file_with_user(SHARED_DIR_NAME, user1, user2, **kwargs)

    step (6, 'Final')

@add_worker
def recipient_worker(step):
    step (2, 'Create workdir')
    d = make_workdir()

    step (5, 'Check permission enforcement for every operation')

    list_files(d)
    run_ocsync(d, user_num=2)
    list_files(d)

    oc = get_oc_api()
    user2 = "%s%i" % (config.oc_account_name, 2)
    oc.login(user2, config.oc_account_password)

    perms = permission_matrix['permission']
    operations_test = OperationsTest(oc, d, SHARED_DIR_NAME)

    sharedDir = os.path.join(d,SHARED_DIR_NAME)
    logger.info ('Checking that %s is present in local directory for recipient_worker', sharedDir)
    expect_exists(sharedDir)
    expect_server_file_exists(user2, SHARED_DIR_NAME)

    for operation in ALL_OPERATIONS:
        # call the matching operation method
        expected_success = operation in permission_matrix['allowed_operations']
        success_message = "allowed"
        if not expected_success:
            success_message = "forbidden"

        error_check(
            getattr(operations_test, operation)(expected_success),
            'Operation "%s" must be %s when share permissions are %i' % (operation, success_message, perms)
        )

    step (6, 'Final')


class OperationsTest(object):
    def __init__(self, oc, work_dir, shared_dir):
        self.oc = oc
        self.work_dir = work_dir
        self.shared_dir = shared_dir
        self._testFileId = 0

    def _make_test_file(self):
        # note: the name doesn't matter for the tests
        test_file = os.path.join(self.work_dir, 'local_test_file_%i.dat' % self._testFileId)
        createfile(test_file, '0', count=1000, bs=1)
        self._testFileId += 1
        return test_file

    def _upload(self, target_file, expected_success):
        test_file = self._make_test_file()
        try:
            logger.info('Upload file to "%s"', target_file)
            self.oc.put_file(target_file, test_file)
        except owncloud.ResponseError as e:
            if e.status_code == 403:
                return not expected_success

            log_response_error(e)
            return False

        if not self._file_exists(target_file):
            logger.error('File %s not actually uploaded', target_file)
            return False

        return expected_success

    def upload(self, expected_success = False):
        target_file = os.path.join(self.shared_dir, 'test_upload.dat')
        return self._upload(target_file, expected_success)

    def upload_overwrite(self, expected_success = False):
        # target the existing file name
        target_file = os.path.join(self.shared_dir, 'overwrite_this.dat')
        return self._upload(target_file, expected_success)

    def _move(self, source_file, target_file, expected_success):
        try:
            logger.info('Move "%s" to "%s"', source_file, target_file)
            self.oc.move(source_file, target_file)
        except owncloud.ResponseError as e:
            if e.status_code == 403:
                return not expected_success

            log_response_error(e)
            return False

        if self._file_exists(source_file) or not self._file_exists(target_file):
            logger.error('%s not actually moved renamed to %s', source_file, target_file)
            return False

        return expected_success

    def rename(self, expected_success = False):
        source_file = os.path.join(self.shared_dir, 'rename_this.dat')
        target_file = os.path.join(self.shared_dir, 'rename_this_renamed.dat')
        return self._move(source_file, target_file, expected_success)

    def move_in(self, expected_success = False):
        test_file = self._make_test_file()
        target_file = 'test_move_in.dat'

        # upload the test file outside the shared dir first
        self.oc.put_file(target_file, test_file)

        # then move that one into the shared dir
        source_file = target_file
        target_file = os.path.join(self.shared_dir, source_file)
        return self._move(source_file, target_file, expected_success)

    def move_in_overwrite(self, expected_success = False):
        test_file = self._make_test_file()
        target_file = 'overwrite_this_through_move_in.dat'

        # upload the test file outside the shared dir first
        self.oc.put_file(target_file, test_file)

        # then move that one into the shared dir
        source_file = target_file
        target_file = os.path.join(self.shared_dir, target_file)
        return self._move(source_file, target_file, expected_success)

    def move_in_subdir(self, expected_success = False):
        source_file = os.path.join(self.shared_dir, 'move_this_to_subdir.dat')
        target_file = os.path.join(self.shared_dir, 'subdir', 'moved_this_to_subdir.dat')
        return self._move(source_file, target_file, expected_success)

    def move_in_subdir_overwrite(self, expected_success = False):
        source_file = os.path.join(self.shared_dir, 'move_this_to_subdir_for_overwrite.dat')
        target_file = os.path.join(self.shared_dir, 'subdir', 'overwrite_this.dat')
        return self._move(source_file, target_file, expected_success)

    def move_out(self, expected_success = False):
        source_file = os.path.join(self.shared_dir, 'move_this_out.dat')
        target_file = 'this_was_moved_out.dat'
        return self._move(source_file, target_file, expected_success)

    def move_out_subdir(self, expected_success = False):
        source_file = os.path.join(self.shared_dir, 'subdir', 'move_this_out.dat')
        target_file = os.path.join(self.shared_dir, 'this_was_moved_out_of_subdir.dat')
        return self._move(source_file, target_file, expected_success)

    def _delete(self, target, expected_success):
        try:
            logger.info('Delete "%s"', target)
            self.oc.delete(target)
        except owncloud.ResponseError as e:
            if e.status_code == 403:
                return not expected_success

            log_response_error(e)
            return False

        if self._file_exists(target):
            logger.error('%s not actually deleted', target)
            return False

        return expected_success

    def delete(self, expected_success = False):
        target = os.path.join(self.shared_dir, 'delete_this.dat')
        return self._delete(target, expected_success)

    def rmdir(self, expected_success = False):
        target = os.path.join(self.shared_dir, 'delete_this_dir')
        return self._delete(target, expected_success)

    def mkdir(self, expected_success = False):
        target = os.path.join(self.shared_dir, 'test_create_dir')

        try:
            logger.info('Create folder "%s"', target)
            self.oc.mkdir(target)
        except owncloud.ResponseError as e:
            if e.status_code == 403:
                return not expected_success

            log_response_error(e)
            return False

        if not self._file_exists(target):
            logger.error('Folder %s not actually created', target)
            return False

        return expected_success

    def _file_exists(self, remote_file):
        try:
            self.oc.file_info(remote_file)
            return True
        except owncloud.ResponseError as e:
            if e.status_code == 404:
                return False
            # unknown error
            raise(e)


def log_response_error(response_error):
    """
    @type response_error: owncloud.ResponseError
    """

    message = response_error.get_resource_body()

    if message[:38] == '<?xml version="1.0" encoding="utf-8"?>':
        import xml.etree.ElementTree as ElementTree

        response_exception = ''
        response_message = ''
        response = message[39:]

        root_element = ElementTree.fromstringlist(response)
        if root_element.tag == '{DAV:}error':
            for child in root_element:
                if child.tag == '{http://sabredav.org/ns}exception':
                    response_exception = child.text
                if child.tag == '{http://sabredav.org/ns}message':
                    response_message = child.text

        if response_exception != '':
            message = 'SabreDAV Exception: %s - Message: %s' % (response_exception, response_message)

    logger.error('Unexpected response: Status code: %i - %s' % (response_error.status_code, message))
    logger.info('Full Response: %s' % (response_error.get_resource_body()))
