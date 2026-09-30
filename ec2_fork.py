#!/usr/bin/env python3

import boto3
import json

client = boto3.client('ec2')

#call describe IMAGES TO KNOW WHAT TO CALL

image_response = client.describe_images(
    Filters=[
        {
            'Name': 'description',
            'Values': ['Amazon Linux 2 AMI*']
        },
        {
            'Name': 'architecture',
            'Values': ['x86_64']
        },
        {
            'Name': 'owner-alias',
            'Values': ['amazon']
        }
    ],
    #DryRun=True
)
    #print(  json.dumps(image_response['Images'][0], indent=4))

#dryrun = True

if image_response['Images']:
    response = client.run_instances(
        ImageId=image_response['Images'][0]['ImageId'],
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=1,
        #DryRun=dryrun
    )
    print(response['Instances'][0]['InstanceId'])
else:
    print("No images found matching the specified filters.")

ec2 = boto3.resource('ec2')
instance = ec2.Instance(response['Instances'][0]['InstanceId'])

instance.reload()
print(f"Instance is {instance.state['Name']}")
print(f"Instance is {instance.state['Name']}")

instance.wait_until_running()

instance.reload()
print(instance.instance_id)

#  ami-08982f1c5bf93d976

#terminate
instance.terminate()
instance.wait_until_terminated()
print(f"Terminating instance {instance.instance_id}")
print
