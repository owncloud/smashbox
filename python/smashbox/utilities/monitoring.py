from smashbox.utilities import *

# simple monitoring to grafana (disabled if not set in config)

def push_to_monitoring(metric, value, test_variable="",timestamp=None):
    monitoring_type = config.get('monitoring_type', None)
    monitoring_host=config.get('monitoring_host',None)
    monitoring_port=config.get('monitoring_port',2003)

    if monitoring_type == 'graphite':
        measurement = '.'.join([config.get('monitoring_push', "cernbox.cboxsls"), config.get('server_name', "localhost"),
                                config.get('runid', "testrun"), test_variable, metric])

        if not monitoring_host:
            return

        if not timestamp:
            timestamp = time.time()

        os.system("echo '%s %s %s' | nc %s %s"%(measurement,value,timestamp,monitoring_host,monitoring_port))
    elif monitoring_type == 'influxdb':
        measurement = "%s,runid=%s,server=%s,testid=%s value=%s"%(
            metric,
            config.get('runid', "testrun"),
            config.get('server_name', "localhost"),
            test_variable,
            value
        )

        os.system("curl -i -XPOST -u %s:%s 'http://%s:%s/write?db=%s' --data-binary '%s'"%(
            config.get('monitoring_user', 'smashbox'),
            config.get('monitoring_password', 'smashbox'),
            monitoring_host,
            monitoring_port,
            config.get('monitoring_push', 'smashbox'),
            measurement
        ))
    else:
        print (config.get('server_name', "localhost"),metric, value, test_variable)


def sizeof_fmt(toConvert, suffix='B'):
    num = toConvert
    units = ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z']
    for i in range(0,len(units)):
        if float(num).is_integer():
            last_num = num
            if abs(last_num) < 1000.0:
                return "%d%s%s" % (last_num, units[i], suffix)
            num /= 1000.0
        else:
            return "%d%s%s" % (last_num, units[i-1], suffix)
    return "%d%s%s" % (toConvert, '', suffix)

def get_file_distr(nfiles, filesize):
    toReturn = "%sf-%s" % (str(nfiles),sizeof_fmt(filesize))
    return toReturn