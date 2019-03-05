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
    """
    Get Intersight alarms via the Intersight API.
    Returns a string with the Critial and Warning alarms counts for the given MOID
    """

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


def get_health(cluster_name, print_name=True):
    """
    Get information including health state of the specified cluster.
    Returns a string of healthy or with alarms counts for the given cluster name
    """
    message = ''
    handle = hyperflex_cluster_api.HyperflexClusterApi(api_instance)
    kwargs = dict(filter="ClusterName eq '%s' or \
        Tags/any(t:t/Key eq 'Location' and t/Value eq'%s')" % (cluster_name, cluster_name))
    try:
        response = handle.hyperflex_clusters_get(**kwargs)
    except Exception as err:
        print(err)
        message = ("There was an error connecting to or retrieving information from Cisco Intersight")

    response_dict = response.to_dict()
    if response_dict.get('results'):
        response_dict = response_dict['results'][0]   # use the 1st result returned
        if print_name:
            message = "Your %s cluster is " % cluster_name
        if response_dict['flt_aggr'] == 0:
            message += 'healthy.  '
        else:   # alarms are present
            message += "reporting alarms.  The %s cluster has " % cluster_name
            message += get_alarms(response_dict['moid'])
            message += '.  '
    else:
        message = "Sorry, I could not find a cluster named %s" % cluster_name

    return message


def get_hx_config_state(cluster_name):
    """
    Get HX cluster configuration state and health via the Intersight API.
    Returns a string with state and health including any alarms present
    """

    handle = hyperflex_cluster_profile_api.HyperflexClusterProfileApi(api_instance)
    kwargs = dict(filter="Name eq '%s' or \
            Tags/any(t:t/Key eq 'Location' and t/Value eq'%s')" % (cluster_name, cluster_name))
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
        message = "Your %s cluster " % cluster_name
        if config_state == 'Associated':
            message += 'is deployed and '
            message += get_health(cluster_name, print_name=False)
            message += '.  '
        elif config_state == 'Assigned':
            message += 'is ready for deployment.  '
        elif config_state == 'Configuring':
            message += 'is currently being deployed.  '
        else:
            message += 'needs additional configuration before being deployed.  '

    return message


def deploy_hx_cluster(cluster_name):
    """Deploy HX cluster via the Intersight API."""

    handle = hyperflex_cluster_profile_api.HyperflexClusterProfileApi(api_instance)
    kwargs = dict(filter="Name eq '%s' or \
            Tags/any(t:t/Key eq 'Location' and t/Value eq'%s')" % (cluster_name, cluster_name))
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
            message = "Your %s cluster is now being deployed.  "\
                "Ask Intersight, what is the status of my %s cluster to get current deployment status" % (cluster_name, cluster_name)

    return message


def get_datacenter_info():
    """Get information including health state of the specified cluster."""
    handle = hyperflex_cluster_profile_api.HyperflexClusterProfileApi(api_instance)
    message = ''
    try:
        response = handle.hyperflex_cluster_profiles_get()
    except Exception as err:
        print(err)
        message = ("There was an error connecting to or retrieving information from Cisco Intersight")

    response_dict = response.to_dict()
    if response_dict.get('results'):
        for cluster in response_dict['results']:
            cluster_name = cluster['name']
            message += get_hx_config_state(cluster_name)
    else:
        message = 'Sorry, I could not find any information for your datacenter clusters'

    return message


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    args = parser.add_argument('-n', '--name', default='Atlanta', help='Name of the HyperFlex cluster to query')
    args = parser.parse_args()
    print(get_datacenter_info())
    print(get_health(args.name))
    print(get_hx_config_state(args.name))
    print(deploy_hx_cluster(args.name))
