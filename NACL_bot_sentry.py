"""
   This Python script automatically removes new NACL ingress rules.
   Amazon EventBridge triggers this Lambda function when AWS CloudTrail detects
   a CreateNetworkAclEntry API event initiated by an IAM user. Next, this Lambda Function
   delete the new entry and send a notification to the admin to report the succesful or failed deletion.
   Outputs get logged and status codes are returned. 
"""

import os
import json
import logging
import boto3
import botocore

# logging
log = logging.getLogger() 
log.setLevel(logging.INFO)

# global variables
NACL_ID = os.environ.get('nacl_id')
SNS_TOPIC_ARN = os.environ['sns_topic_arn']
if NACL_ID is None:
    raise Exception("NACL ID not found")

# instantiate boto3 resource
ec2_resource = boto3.resource('ec2')
NETWORK_ACL = ec2_resource.NetworkAcl(NACL_ID)


def lambda_handler(event, context):
    event_detail = event.get('detail', {})
    if delete_nacl_entry(event_detail):
        log.info("deleteEntry: Successful")
        if send_notification(event_detail):
            log.info("SNS publish: Successful")
            return {
                'statusCode': 200,
                'body': json.dumps({'message': "Successful requests."})
            }
        log.info("SNS publish: an error occurred")    
        return {
            'statusCode': 206,
            'body': json.dumps({'error': "An error occurred in the SNS publish request."})
        }
        
    if not send_notification(event_detail, False):
        log.info("deleteEntry: an error occurred")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': "an error occurred in the deleteEntry request."})
        }


def delete_nacl_entry(event_detail):
    """
    From the event_detail object, parses the egress and ruleNumber value
    and call the delete_entry method, deleting the new NACL rule.
    Returns True if successful, if error occurs, log the error and returns False.
    """
    request_parameters = event_detail['requestParameters']
    try:
        NETWORK_ACL.delete_entry(
            Egress=request_parameters['egress'],
            RuleNumber=request_parameters['ruleNumber']
            )
        return True 
    except botocore.exceptions.ClientError as error:
        log.error(f"Boto3 API returned error: {error}")
        return False 


def send_notification(event_detail, success=True):
    """
    Parses information about the user and the event, creates a message accordingly,
    sends a notification via AWS SNS to the topic saved in the environment variables. 
    Returns True if successful, if an error occurs, log the error and returns False.
    """
    request_parameters = event_detail['requestParameters']
    user_identity = event_detail['userIdentity']
    
    message = "A new NACL entry is being created but the deleteEntry request has failed.\n"
    subject = "WARNING: Auto-Mitigation unsuccessful"
    if success:
        message = "AUTO-MITIGATED: Entry rule succesfully removed from NetworkAcl\n"
        subject = "Auto-Mitigation successful"
        
    message += (
            f"NetworkAcl ID: {request_parameters['networkAclId']}\n"
            f"added by: {user_identity['arn']} - ID number: {user_identity['accountId']}\n"
            f"rule_number: {request_parameters['ruleNumber']}\n"
            f"rule_action: {request_parameters['ruleAction']}\n"
            f"port_range: {request_parameters['portRange']}\n"
            f"acl_protocol: {request_parameters['aclProtocol']}\n"
            f"cidr_block: {request_parameters['cidrBlock']}\n"
            ) 
    try:
        boto3.client('sns').publish(TargetArn=SNS_TOPIC_ARN, Message=message, Subject=subject)
        return True
    except botocore.exceptions.ClientError as error:
        log.error(f"Boto3 API returned error: {error}")
        return False
