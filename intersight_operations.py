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
from intersight.apis import fault_instance_api

def get_faults():
  """Get Intersight Faults via the Intersight API."""

  try:
    api_instance = IntersightApiClient(
      host="https://intersight.com/api/v1",
      private_key="SecretKey.txt", 
      api_key_id="59dd1f1916267c00015e0929/59dd1ec316267c00015e0496/5b0edbde68306b6e34173261"
    )

    # GET Faults
    handle   = fault_instance_api.FaultInstanceApi(api_instance)
    response = handle.fault_instances_get()

    # Create a unique list of the severity types in the response
    severities = [fault.severity for fault in response._results]

    # Create a message with a count of each severity type that was in the response
    message = ("For the requested Intersight fault retrieval operation, there are ")

    for severity in set([fault.severity for fault in response._results]):
      message += str(sum(f.severity == severity for f in response._results)) + " " + severity + " faults, "

  except Exception as err:
    print err
    message = ("There was an error connecting to or retrieving information from Cisco Intersight")

  return message

if __name__ == "__main__":
    print(get_faults())
