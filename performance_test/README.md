# Performance Tests

THIS WORK IS IN PROGRESS

## Prerequisites

Install owncloud client, as described at
> https://software.opensuse.org/download/package?project=isv:ownCloud:desktop&package=owncloud-client

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
