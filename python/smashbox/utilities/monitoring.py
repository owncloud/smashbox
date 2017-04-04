from smashbox.utilities import reflection, config, os
import smashbox.utilities

def push_to_local_monitor(metric, value):
    print metric, value

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

def push_to_monitoring(returncode, total_duration):
    shared = reflection.getSharedObject()
    if not 'monitoring_points' in shared.keys():
        return

    monitoring_points = shared['monitoring_points']
    monitoring_type = config.get('monitoring_type', None)
    if monitoring_type == 'prometheus':
        monitoring_endpoint = config.get('endpoint', None)
        release = config.get('owncloud', None)
        client = config.get('client', None)
        suite = config.get('suite', None)
        build = config.get('build', None)
        duration_label = config.get('duration_label', None)
        queries_label = config.get('queries_label', None)

        points_to_push = []

        # total duration is default for jenkins if given
        if duration_label is not None:
            points_to_push.append('%s{owncloud=\\"%s\\",client=\\"%s\\",suite=\\"%s\\",build=\\"%s\\",exit=\\"%s\\"} %s'%(
                duration_label,
                release,
                client,
                suite,
                build,
                returncode,
                total_duration))

        # No. queries is default for jenkins if given
        if queries_label is not None:
            # TODO: add number of queries from log
            no_queries = 0
            points_to_push.append('%s{owncloud=\\"%s\\",client=\\"%s\\",suite=\\"%s\\",build=\\"%s\\",exit=\\"%s\\"} %s'%(
                queries_label,
                release,
                client,
                suite,
                build,
                returncode,
                no_queries))

        # Other points are not supported in jenkins yet
        for monitoring_point in monitoring_points:
            continue

        # Push to monitoring all points to be pushed
        for point_to_push in points_to_push:
            cmd = "echo \"%s\" | curl --data-binary @- %s"%(point_to_push,monitoring_endpoint)
            smashbox.utilities.log_info('Pushing to monitoring: %s'%cmd)
            os.system(cmd)

    elif monitoring_type == 'local':
        for monitoring_point in monitoring_points:
            push_to_local_monitor(monitoring_point['metric'], monitoring_point['value'])
        push_to_local_monitor("returncode", returncode)
        push_to_local_monitor("elapsed", total_duration)