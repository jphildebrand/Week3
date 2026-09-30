"""Create, inspect, tag, and terminate an Amazon Linux EC2 instance."""

import boto3
from botocore.exceptions import ClientError


REGION = "us-east-1"
DRYRUN = False
TAG_NAME = "Name"
TAG_VALUE = "Jeffrey"


def get_image(ec2_client):
    """Return the first Amazon Linux 2 x86_64 AMI returned for the region."""
    # The filters avoid hard-coding an AMI ID that may become outdated.
    images = ec2_client.describe_images(
        Filters=[
            {
                "Name": "description",
                "Values": ["Amazon Linux 2 AMI*"],
            },
            {
                "Name": "architecture",
                "Values": ["x86_64"],
            },
            {
                "Name": "owner-alias",
                "Values": ["amazon"],
            },
        ]
    )
    # The full response lists hundreds of AMIs, so only the count is printed to keep output readable.
    print(f"AMI lookup found {len(images['Images'])} matching images")

    if not images["Images"]:
        raise RuntimeError("No matching Amazon Linux AMI was found.")

    image_id = images["Images"][0]["ImageId"]
    print(f"Selected AMI: {image_id}")
    return image_id


def create_ec2(ami, ec2_client):
    """Create one EC2 instance and return its instance ID."""
    # run_instances returns a dictionary containing the new instance details.
    response = ec2_client.run_instances(
        ImageId=ami,
        InstanceType="t2.micro",
        MaxCount=1,
        MinCount=1,
        DryRun=DRYRUN,
    )
    # Only the instance ID is needed; main() turns it into a resource object for further actions.
    return response["Instances"][0]["InstanceId"]


def main():
    """Run the EC2 lifecycle and clean up the instance when finished."""
    ec2_client = boto3.client("ec2", region_name=REGION)
    ami = get_image(ec2_client)

    try:
        instance_id = create_ec2(ami, ec2_client)
    except ClientError as error:
        # AWS raises DryRunOperation instead of creating an instance in dry-run mode.
        if DRYRUN and error.response["Error"]["Code"] == "DryRunOperation":
            print("Dry run succeeded: the instance would have been created.")
            return
        raise

    # A resource object exposes convenient instance actions and attributes.
    ec2 = boto3.resource("ec2", region_name=REGION)
    instance = ec2.Instance(instance_id)
    print(f"Instance ID: {instance.instance_id}")

    try:
        # Wait before reading the public address because it is unavailable while pending.
        instance.wait_until_running()
        instance.reload()
        print(f"Instance is {instance.state['Name']}")
        print(f"Public IP: {instance.public_ip_address}")
        print(f"Tags before update: {instance.tags}")

        # create_tags adds the Name tag to the existing instance; reload() refreshes the cached attributes.
        instance.create_tags(Tags=[{"Key": TAG_NAME, "Value": TAG_VALUE}])
        instance.reload()
        print(f"Tags after update: {instance.tags}")
    finally:
        # Always terminate the temporary resource so testing does not leave charges behind.
        instance.terminate()
        instance.wait_until_terminated()
        instance.reload()
        print(f"Instance is {instance.state['Name']}")


if __name__ == "__main__":
    main()