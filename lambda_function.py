"""
Name:
    lambda_function.py
Purpose:
    lambda function for the Intersight Skill
    Feature 1:
    Q: What is the health of my <location> HX cluster? (e.g., Atlanta)
    A: Your <location> cluster is currently <overall health>.  (e.g., Atlanta, healthy/reporting alarms)

    Feature 2:
    Q: What is the configuration status of my <location> HX cluster?
    A: Your <location> cluster is <status> (assigned/associated)

    Feature 3:
    Q: Deploy the <location> cluster.
    A: Deployment has been requested on your <location> cluster.
Author:
    John McDonough (jomcdono@cisco.com)
    Cisco Systems, Inc.
"""

from __future__ import print_function

# Import the intersight functions
import intersight_hx_operations

# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Alexa Skill for Cisco Intersight.  " \
                    "You can say things like, How are my data centers?  " \
                    "Or you can ask me to perform an action like deploying a cluster.  " \
                    "For example, Deploy my Atlanta cluster.  "
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Did you want to do something with, or know something about Cisco Intersight?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using the Alexa Skill for Cisco Intersight."

    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    session_attributes = {}
    reprompt_text = None

    # Dispatch to skill's intent handlers
    if intent_name == "GetDCInfo":         # Entry point for the GetInfo intent
        speech_output = intersight_hx_operations.get_datacenter_info()
    elif intent_name == "GetHealth":
        speech_output = intersight_hx_operations.get_health(intent['slots']['name']['value'])
    elif intent_name == "GetHXConfigState":
        speech_output = intersight_hx_operations.get_hx_config_state(intent['slots']['name']['value'])
    elif intent_name == "DeployHXCluster":
        speech_output = intersight_hx_operations.deploy_hx_cluster(intent['slots']['name']['value'])
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

    should_end_session = True

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
