from smashbox.utilities import *

__doc__ = """

Test basic file sharing by link

Covers:
 * https://github.com/owncloud/core/pull/19619

"""


filesize_kb = int(config.get('share_filesizeKB', 10))


@add_worker
def setup(step):

    step(1, 'create test users')
    reset_owncloud_account(num_test_users=2)
    check_users(2)

    reset_rundir()
    reset_server_log_file()

    step(6, 'Validate server log file is clean')

    d = make_workdir()
    scrape_log_file(d)


@add_worker
def sharer(step):

    step(2, 'Create workdir')
    d = make_workdir()

    step(3, 'Create initial test files and directories')

    proc_name = reflection.getProcessName()
    dir_name = "%s/%s" % (proc_name, 'localShareDir')
    local_dir = make_workdir(dir_name)

    createfile(os.path.join(local_dir, 'TEST_FILE_LINK_SHARE.dat'), '0', count=1000, bs=filesize_kb)
    shared = reflection.getSharedObject()
    shared['md5_sharer'] = md5sum(os.path.join(local_dir, 'TEST_FILE_LINK_SHARE.dat'))

    list_files(d)
    run_ocsync(d, user_num=1)
    list_files(d)

    step(4, 'Sharer shares file as link')

    oc_api = get_oc_api()
    oc_api.login("%s%i" % (config.oc_account_name, 1), config.oc_account_password)

    kwargs = {'perms': 31}
    share = oc_api.share_file_with_link(os.path.join('localShareDir', 'TEST_FILE_LINK_SHARE.dat'), **kwargs)
    shared['SHARE_LINK_TOKEN'] = share.token


@add_worker
def public_downloader(step):

    step(2, 'Create workdir')
    d = make_workdir()

    step(5, 'publicDownloader downloads and validates the file\'s integrity')

    shared = reflection.getSharedObject()
    url = oc_webdav_url(
        remote_folder=os.path.join('index.php', 's', shared['SHARE_LINK_TOKEN'], 'download'),
        webdav_endpoint=config.oc_root
    )

    download_target = os.path.join(d, 'TEST_FILE_LINK_SHARE.dat')
    runcmd('curl -k %s -o %s %s' % (config.get('curl_opts', ''), download_target, url))
    expect_not_modified(download_target, shared['md5_sharer'])
