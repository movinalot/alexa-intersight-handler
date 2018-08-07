"""
Name:
    intersight_operations.py
Purpose:
    Intersight functions for the Intersight Skill
Author:
    John McDonough (jomcdono@cisco.com)
    Cisco Systems, Inc.
"""

from intersight.intersight_api_client import IntersightApiClient
from intersight.apis import cond_alarm_api
from intersight.apis import hyperflex_cluster_profile_api
from intersight.apis import hyperflex_cluster_api

api_instance = IntersightApiClient(
    host="https://intersight.com/api/v1",
    private_key="soperspam1_ucstechtalks_SecretKey.txt",
#    private_key="/Users/dsoper/Downloads/SSOSecretKey.txt",
    api_key_id="5a3404ac3768393836093cab/5b02fa7e6d6c356772394170/5b02fad36d6c356772394449"
#    api_key_id="596cc79e5d91b400010d15ad/596cc7945d91b400010d154e/5b6275df3437357030a7795f"
)


def get_alarms(moid):
    """Get Intersight alarms via the Intersight API."""

    message = ''
    # GET Alarms
    handle = cond_alarm_api.CondAlarmApi(api_instance)
    kwargs = dict(filter="AffectedMoId eq '%s'" % moid)
    try:
        response = handle.cond_alarms_get(**kwargs)
    except Exception as err:
        print(err)
        return 'There was an error connecting to or retrieving information from Cisco Intersight'

    # Critical and Warning alarms
    response_dict = response.to_dict()
    if response_dict.get('results'):
        critical_count = sum(alarm['severity'] == 'Critical' for alarm in response_dict['results'])
        and_str = ''
        plural = ''
        if critical_count != 0:
            if critical_count > 1:
                plural = 's'
            message += "%d Critical alarm%s" % (critical_count, plural)
            and_str = ' and '
        plural = ''
        warning_count = sum(alarm['severity'] == 'Warning' for alarm in response_dict['results'])
        if warning_count != 0:
            if warning_count > 1:
                plural = 's'
            message += "%s%d Warning alarm%s" % (and_str, warning_count, plural)

    return message


def get_hx_config_state(cluster_name):
    """Get HX cluster configuration state via the Intersight API."""

    handle = hyperflex_cluster_profile_api.HyperflexClusterProfileApi(api_instance)
    kwargs = dict(filter="Name eq '%s'" % cluster_name)
    try:
        response = handle.hyperflex_cluster_profiles_get(**kwargs)
    except Exception as err:
        print(err)
        return 'There was an error connecting to or retrieving information from Cisco Intersight'

    message = ''
    response_dict = response.to_dict()
    if response_dict.get('results'):
        # get the 1st results object if a list was returned
        response_dict = response_dict['results'][0]
        config_state = response_dict['config_context']['config_state']
        message = "Your %s cluster is currently in the %s state " % (cluster_name, config_state)
        if config_state == 'Assigned':
            message += 'and is ready to be deployed'

    return message


def deploy_hx_cluster(cluster_name):
    """Deploy HX cluster via the Intersight API."""

    handle = hyperflex_cluster_profile_api.HyperflexClusterProfileApi(api_instance)
    kwargs = dict(filter="Name eq '%s'" % cluster_name)
    try:
        response = handle.hyperflex_cluster_profiles_get(**kwargs)
    except Exception as err:
        print(err)
        return 'There was an error connecting to or retrieving information from Cisco Intersight'

    message = ''
    response_dict = response.to_dict()
    if response_dict.get('results'):
        # get the 1st results object if a list was returned
        response_dict = response_dict['results'][0]
        if response_dict['config_context']['config_state'] == 'Associated':
            message = "Your %s cluster is already deployed and in the Associated state" % cluster_name
        else:   # config_state != 'Associated'
            moid = response_dict['moid']
            api_body = dict(Action='Deploy')
            response = handle.hyperflex_cluster_profiles_moid_patch(moid, api_body)
            message = "Your %s cluster is now being deployed.  Ask what is the configuration status of my %s cluster to get current deployment status" % (cluster_name, cluster_name)

    return message


def get_cluster_info(cluster_name):
    """Get information including health state of the specified cluster."""
    try:
        handle = hyperflex_cluster_api.HyperflexClusterApi(api_instance)
        kwargs = dict(filter="ClusterName eq '%s'" % cluster_name)
        response = handle.hyperflex_clusters_get(**kwargs)
        response_dict = response.to_dict()
        if response_dict.get('results'):
            message = "Your %s cluster is currently " % cluster_name
            response_dict = response_dict['results'][0]   # use the 1st result returned
            if response_dict['flt_aggr'] == 0:
                message += 'healthy'
            else:   # alarms are present
                message += "reporting alarms.  The %s cluster has " % cluster_name
                message += get_alarms(response_dict['moid'])
        else:
            message = "Sorry, I could not find a cluster named %s" % cluster_name

    except Exception as err:
        print(err)
        message = ("There was an error connecting to or retrieving information from Cisco Intersight")

    return message


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    args = parser.add_argument('-n', '--name', required=True, help='Name of the HyperFlex cluster to query')
    args = parser.parse_args()
    print(get_cluster_info(args.name))
    print(get_hx_config_state(args.name))
    print(deploy_hx_cluster(args.name))
