# Import boto3 (AWS SDK for Python) and ClientError so we can catch AWS API errors -JH ####
import boto3
from botocore.exceptions import ClientError

# When True, AWS only checks whether the request would succeed and creates nothing; False launches a real instance -JH ####
DRYRUN = False


# Looks up the latest Amazon Linux 2 AMI for the client's region so we never hardcode an AMI id -JH ####
def Get_Image(ec2_client):
    """Return the latest Amazon Linux 2 AMI id for the client's region."""
    # Filter to Amazon-owned, x86_64 images whose description starts with "Amazon Linux 2 AMI" -JH ####
    images = ec2_client.describe_images(
        Filters=[
            {'Name': 'description', 'Values': ['Amazon Linux 2 AMI*']},
            {'Name': 'architecture', 'Values': ['x86_64']},
            {'Name': 'owner-alias', 'Values': ['amazon']},
        ]
    )
    # Sort newest first so [0] is the actual latest AMI, then return its id -JH ####
    sorted_images = sorted(images['Images'], key=lambda i: i['CreationDate'], reverse=True)
    return sorted_images[0]['ImageId']


# Launches one t2.micro instance from the given AMI and returns its instance id -JH ####
def Create_EC2(AMI, ec2_client):
    """Launch one t2.micro from the AMI and return the instance id."""
    response = ec2_client.run_instances(
        ImageId=AMI,
        InstanceType='t2.micro',
        MaxCount=1,
        MinCount=1,
        DryRun=DRYRUN,
    )
    return response['Instances'][0]['InstanceId']


# Main workflow: find the AMI, create the instance, wait for it to run, then terminate it -JH ####
def main():
    # Create the low-level client used for describe_images and run_instances -JH ####
    ec2_client = boto3.client('ec2', region_name='us-east-1')

    # Get the latest AMI id -JH ####
    ami = Get_Image(ec2_client)
    print(f"Using AMI: {ami}")

    # Create the instance; a DryRunOperation error just means the dry run would have succeeded -JH ####
    try:
        instance_id = Create_EC2(ami, ec2_client)
    except ClientError as e:
        if e.response['Error']['Code'] == 'DryRunOperation':
            print(f"Dry run: the request would have succeeded ({e})")
            return
        raise

    # Turn the instance id into an Instance object so we can run actions on it -JH ####
    ec2 = boto3.resource('ec2', region_name='us-east-1')
    instance = ec2.Instance(instance_id)
    print(instance.instance_id)

    # Wait until the instance is running, then print its state -JH ####
    instance.wait_until_running()
    instance.reload()
    print(f"Instance is {instance.state['Name']}")

    # Terminate the instance, wait until it is gone, then print its final state -JH ####
    instance.terminate()
    instance.wait_until_terminated()
    instance.reload()
    print(f"Instance is {instance.state['Name']}")


# Only run main() when the script is executed directly, not when imported -JH ####
if __name__ == '__main__':
    main()
