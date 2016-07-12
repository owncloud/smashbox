from smashbox.utilities import *

def run_sync(local_folder, remote_folder="", n=None, user_num=None):
    """
    Overwrite for sync
    """
    run_ocsync(local_folder, remote_folder, n, user_num)

def prepare_sync(d):
    """
    Prepares the sync
    """
