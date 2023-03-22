# Introduction
NACL Sentry function:

The bot automatically deletes new rules added to a NACL and sends an email notification containing information about those changes.


# Workflow
1. a new rule is added to the network acl.
2. a CloudWatch event triggers the Lambda function
3. the script deletes the new entry
4. an email notification is sent via SNS with information about the change, who made it and confirm the change was reverted.

# Pre-requisite
- CloudTrail has to be enabled in the AWS Region where the solution is deployed
- VPC with custom nacl rules 
- IAM role for the Lambda with EC2 permissions (more restrictive permission can be applied accordingly).
- os, json, boto3 modules installed

# Instructions
1. Make sure a Trail in ***CloudTrail*** is created to enable logs in the region where the bot will operate.
This allows the Lambda function to use the event log to parse information about the API call.

2. ***Create the VPC*** and ***create the default NACL rules***.
The bot is set to work on inbound rules only.
The inbound rules created before deploying the Lambda function will be considered the default state.
From the deployment of the Lambda function, any new inbound rule will be deleted.

3. ***Create the IAM role*** for the Lamba function:
Attach the EC2FullAccess policy type (we will use full permission for the testing but it’s best practice to apply the principle of least privilege).
Name it and create it.
Make sure that this role has the following policies attached:

- AWSLambdaBasicExecutionRole

- AWSLambdaSNSPublishPolicyExecutionRole

    And relative permission to access EC2

4. ***Create the Lambda*** Function:
add the code provided in this repository
update the global variables (global variables can be found at the beginning of the script). 
create the following environment variables: 

nacl_id : insert the Nacl ID

sns_topic_arn : insert the SNS topic ARN

Please find instructions on how to create the SNS topic at step number 6

5. ***Add CloudWatch event*** as trigger:
From the function overview, select “add trigger”	
Select EventBridge as a source
Select “create a new rule” and name it
Select "event pattern" as rule type,  EC2 from the first drop-down menu,  AWS API call via CloudTrail from the second drop-down menu
Under Detail, thick the "operation" box and select the following operation:

- CreateNetworkAclEntry

    Add the trigger and save changes

6. ***Create the SNS Topic***:
Create a new topic, Standard type
Name it
Any other setting can be left as default
Create now a Subscription:
Under “Protocol” select Email and under “endpoint” insert the email address
Any other setting can be left as default
Create the subscription. 
Confirm subscription by clicking on the link sent to the email address used in the subscription

7. Add ***Amazon SNS*** as destination:
From the function overview select “add destination”
Under “destination” simply select the topic created in step 5. If the topic doesn’t appear in the drop-down menu, please click the refresh button next to it.

8. ***Test*** the function:
Add an inbound rule to the network Acl of your VPC. Adding this rule creates an EC2 CreateNetworkAclEntry service event, which trigger the Lambda function. 
After refreshing a couple of times, the new inbound rule should disappear and you should receive an email with the relative information.


For debugging purpose, a JSON file with a sample of the CreateNetworkAclEntry event is added to this repository. 
