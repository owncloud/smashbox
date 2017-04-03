from smashbox.utilities import *
from smashbox.utilities import reflection

def commit_to_monitoring(metric,value,timestamp=None):
    shared = reflection.getSharedObject()
    if not 'monitoring_points' in shared.keys():
        shared['monitoring_points'] = []

    # Create monitoring metric point
    monitoring_point = dict()
    monitoring_point['metric'] = metric
    monitoring_point['value'] = value
    monitoring_point['timestamp'] = timestamp

    # Append metric to shared object
    monitoring_points = shared['monitoring_points']
    monitoring_points.append(monitoring_point)
    shared['monitoring_points'] = monitoring_points

def push_to_monitoring(returncode):
    shared = reflection.getSharedObject()
    if not 'monitoring_points' in shared.keys():
        return

    monitoring_type = config.get('monitoring_type', None)
    if monitoring_type == 'cernbox':
        monitoring_host = config.get('monitoring_host', None)
        monitoring_port = config.get('monitoring_port', 2003)

        if not monitoring_host:
            return

        monitoring_points = shared['monitoring_points']
        for monitoring_point in monitoring_points:
            timestamp = monitoring_point['timestamp']
            if not timestamp:
                timestamp = time.time()

            os.system("echo '%s %s %s' | nc %s %s" % (monitoring_point['metric'],  monitoring_point['value'], timestamp, monitoring_host, monitoring_port))
    else:
        monitoring_points = shared['monitoring_points']
        for monitoring_point in monitoring_points:
            print monitoring_point['metric'], monitoring_point['value']
        print "returncode", returncode