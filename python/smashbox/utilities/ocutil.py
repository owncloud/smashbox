from smashbox.script import config
from smashbox.utilities import *

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

    cmd = 'rsync -a --chown=www-data:www-data --chmod=777 mount.json root@%s:%s/%s/.' % (config.oc_server, config.oc_server_datadirectory, user_name)
    rtn_code = runcmd(cmd)



