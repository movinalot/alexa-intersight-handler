"""
Name:
    intersight_operations.py
Purpose:
    Intersight functions for the Intersight Skill
Author:
    John McDonough (jomcdono@cisco.com)
    Cisco Systems, Inc.
"""

import sys
import json
from intersight.intersight_api_client import IntersightApiClient
from intersight.apis import cond_alarm_api
from intersight.apis import hyperflex_cluster_profile_api

api_instance = IntersightApiClient(
    host="https://intersight.com/api/v1",
    private_key="soperspam1_ucstechtalks_SecretKey.txt",
    api_key_id="5a3404ac3768393836093cab/5b02fa7e6d6c356772394170/5b02fad36d6c356772394449"
)


def get_alarms():
    """Get Intersight Faults via the Intersight API."""

    try:
        # GET Alarms
        handle = cond_alarm_api.CondAlarmApi(api_instance)
        kwargs = dict(top=2000)
        response = handle.cond_alarms_get(**kwargs)

        # Create a unique list of the severity types in the response
        severities = [alarm.severity for alarm in response._results]

        # Create a message with a count of each severity type that was in the response
        message = ("For the requested Intersight alarm retrieval operation, there are ")

        for severity in set([alarm.severity for alarm in response._results]):
            message += str(sum(f.severity == severity for f in response._results)) + " " + severity + " alarms, "

    except Exception as err:
        print(err)
        message = ("There was an error connecting to or retrieving information from Cisco Intersight")

    return message


def get_hx_config_state():
    """Deploy HX cluster via the Intersight API."""

    try:
        handle = hyperflex_cluster_profile_api.HyperflexClusterProfileApi(api_instance)
        kwargs = dict(filter="Name eq 'sjc07-r13-hx-edge-4'")
        response = handle.hyperflex_cluster_profiles_get(**kwargs)

        response_dict = response.to_dict()
        if response_dict.get('results'):
            # get the 1st results object if a list was returned
            response_dict = response_dict['results'][0]
            message = 'Your Intersight HyperFlex cluster is currently in the ' + response_dict['config_context']['config_state'] + ' state'

    except Exception as err:
        print(err)
        message = ("There was an error connecting to or retrieving information from Cisco Intersight")

    return message


if __name__ == "__main__":
    print(get_alarms())
    print(get_hx_config_state())
