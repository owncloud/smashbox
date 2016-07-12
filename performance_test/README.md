# Performance Tests

Smashbox default tests are mostly designed to check client and server in various complex and usually rare synchronisation scenarious, testing both synchronisation algorithm on the client and server code/configuration.

Currently smashbox also supports some performance tests:

* lib/test)userload.py: 1 uploader sync to the account and in parallel 5 downloaders start syncing down the changes from that account.
- typical scenario, but probably would need to be extended on scenario with 1 uploader to shared folder and 5 downloaders subsribed on that share.

* lib/test_nplusone.py: this test is using one uploader in one downloader to the client. This test is typical load generator on different types distribution
- most popular tests are 1000 files of 10kB, 100 files of 100kB, 10 files of 10MB and 1 file of 100MB. This verifies both small files, normal scenario and big files chunked upload.

* lib/test_storm.py: 10 uploaders sync to the same account at the same time, and after that 10 users sync down the change from the same account
- above test is stress testing the server ability to sync from many clients to the same account.
- this test is not frequent sync scenario since user would need to have 10 separate client and add files to them at the same time.

Future plan:
- design the test, which will sync the distribution of files based on the probability that this file could be synced and predefined usual number of this files in the sync. One smashbox run will generate some random load.

## Prerequisites

Install owncloud client, as described at
> https://software.opensuse.org/download/package?project=isv:ownCloud:desktop&package=owncloud-client

```
apt-get update
apt-get install git-all
apt-get install curl
apt-get install python-pycurl
apt-get install python-netifaces
apt-get install python-numpy
```

```
git clone https://github.com/owncloud/smashbox.git
cd smashbox
```

For newest updates:
```
git checkout general-performance-tests
```

## First Smashbox Deamon run

> usage: smashbox-deamon [-h] [--configs CONFIGS]
>
> This is the deamon to run multiple configs in the sequential manner
>
> optional arguments:
>   -h, --help         show this help message and exit
>   --configs CONFIGS  specifies target config for the test execution e.g.
>                      performance/smashbox-deamon.json

```
smashbox/performance_test/smashbox-deamon
```

Optionaly:
```
smashbox/performance_test/smashbox-deamon --configs PATH_TO_YOUR_CONFIG/YOUR_SMASHBOX_DEAMON_CONFIG.json
```

Prompt will ask you to edit the config file with the new config file `/home/mrow4a/smashbox/performance_test/smashbox-deamon.json`.

## Configure smashbox-deamon

###General layout:

<pre>
   smashbox-deamon.json
   ├── config                                   : specifies the server configuration
   ├── loop                                     : int, specifies the number of loops the deamon should repeat the tests
   ├── tests                                    : array containing json structured test details
   └── loop                                     : int, if test takes too long, terminate after that time
</pre>

###Exemplary json:

```
{
    "tests" :
    [
        {
            "performance_test/test_gen_nplusone.py": {
                "nplusone_filesize": {
                    "value": "100",
                    "type": "int",
                    "_DESCRIPTION": "Specifies the size in Bytes of single test file"
                },
                "nplusone_nfiles": {
                    "value": "1",
                    "type": "int",
                    "_DESCRIPTION": "Specifies the number of test files"
                },
                "nplusone_fscheck": {
                    "value": "False",
                    "type": "bool",
                    "_DESCRIPTION": "Decide if to run checksum check on each file"
                }
            }
        },
        {
            "performance_test/test_gen_nplusone.py": {
                "nplusone_filesize": {
                    "value": "100000",
                    "type": "int",
                    "_DESCRIPTION": "Specifies the size in Bytes of single test file"
                },
                "nplusone_nfiles": {
                    "value": "10",
                    "type": "int",
                    "_DESCRIPTION": "Specifies the number of test files"
                },
                "nplusone_fscheck": {
                    "value": "True",
                    "type": "bool",
                    "_DESCRIPTION": "Decide if to run checksum check on each file"
                }
            }
        }
    ],
    "loop" : 1,
    "config" : [
        "performance_test/owncloud-example.json",
        "performance_test/dropbox-example.json"
    ],
    "timeout" : 3600,
    "_DESCRIPTION" : "Please refer to github repository. This field could also server as a comment field for this config file"
}
```

###Recommended test - test_gen_nplusone.py

Test [gen_nplusone](performance/test_gen_nplusone.py) is a modified version of nplusone test. Description according to __doc__:
```
Add nfiles to a directory and check consistency.
The consistency will be checked by first, synchronising nfiles to the server from one sync-client (worker) process,
and the other sync-client process will be syncing down the added nfiles.
```


The above configuration tells that smashbox-deamon should use 2 server config files, `performance_test/owncloud-example.json` and `performance_test/dropbox-example.json`.
Using this 2 server config files, it will execute for each of them sequentialy, two test cases, with 1 files of 100 Bytes, and 10 files of 100kB, one with checksuming and the other without.

###Setting server config file:

Server config has to be set according to the [example](owncloud-example.json)

Using that method, your script will access the server via ssh(has to have passwordless access), delete the test user if exists, create a new one and perform the single test. That operation will be performed for each test case.

TODO: Test using predefined test account, authenticating with simple user name and password, deleting the content of directory, performing the test in clean directory.

### InfluxDB database installation

Before installing smashbox l, and to use all of their capabilities, there is a need of installing InfluxDB to store the results of the working scripts.

You can both install InfluxDB via the instructions from the official repository:

```https://influxdata.com/```

or use the preconfigured source using the docker container:

```docker run --restart=always --name influxdb -d -p 8083:8083 -p 8086:8086 -e INFLUXDB_HTTP_AUTH_ENABLED="true" -e INFLUXDB_REPORTING_DISABLED="true" tutum/influxdb```

CONFIGURATION EXAMPLE:

Enter the site at which you host the docker, e.g. localhost:8083

CREATE USER <username> WITH PASSWORD '<password>' WITH ALL PRIVILEGES

CREATE DATABASE "smashbox"

CREATE USER "demo" WITH PASSWORD 'demo'

GRANT ALL/READ/WRITE on smashbox to demo

Access the database container
sudo docker exec -it influxdb /bin/bash -c "export TERM=xterm; exec bash"

If needed, change configuration file, updating
nano /etc/influxdb/influxdb.conf

apt-get upgrade influxdb

Restart container (after exiting container, on the host)
docker restart influxdb

TO BE COMPATILIBLE WITH GRAFANA TEMPLATED DASHBOARDS, YOU NEED TO NAME DATABASE smashbox

Under port 8083 you can reach web server InfluxDB:
> http://localhost:8083

Data Need to be feed into the database using port 8086:
> http://localhost:8086

### Grafana installation

```
sudo docker run --restart=always --name grafana -i -d -p 3000:3000 grafana/grafana
```

Under port 3000 you can reach web server Grafana
> http://localhost:3000

To configure it use:
```
docker exec -it grafana /bin/bash -c "export TERM=xterm; exec bash"
```

Change the grafana settings inside the image.

`nano /etc/grafana/grafana.ini`

Github authentication, configuration and more at:

`http://docs.grafana.org/installation/configuration/`

More at `https://www.youtube.com/watch?v=QhhwzgAKd9U`

## Killing smashbox processes

If for some reason, you need to kill smashbox processes, use:
```
ps -ef | grep smashbox | grep -v grep | awk '{print $2}' | xargs kill -9
```

## Daily update script
Smashbox tool [json-config-daily-update](https://github.com/owncloud/smashbox/blob/general-performance-tests/performance_test/json-config-daily-update) gives a possibility of daily update of the smashbox runid the the present date.

```
sudo crontab -e
```

Example crontab:
```
0 8 * * * apt-get -y install owncloud-client  > /dev/null 2>&1
0 8 * * * /home/testy/smashbox/performance_test/json-config-daily-update /home/testy/smashbox/performance_test/owncloud90.json  > /dev/null 2>&1
0 8 * * * /home/testy/smashbox/performance_test/json-config-daily-update /home/testy/smashbox/performance_test/owncloud9mas.json  > /dev/null 2>&1
*/20 * * * * /home/testy/smashbox/performance_test/smashbox-deamon  > /dev/null 2>&1
```

However, before you run smashbox, install database (currently supported Graphite) and web server for results display (e.g. Grafana).

## Dropbox client support
TODO:
For more info, refer to:
https://hub.docker.com/r/mrow4a/smashbox/

## Seafile client support
TODO:
For more info, refer to:
https://hub.docker.com/r/mrow4a/smashbox/

## Dockerised smashbox old version - outdated
TODO:
For more info, refer to:
https://hub.docker.com/r/mrow4a/smashbox/