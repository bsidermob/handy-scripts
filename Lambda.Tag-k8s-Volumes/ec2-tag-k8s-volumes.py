import boto3
import os
from datetime import datetime, timedelta
from dateutil.parser import *

# This tags volumes which belong to Kubernetes
# as this isn't done neither by KOPS nor by
# AWS autoscaling groups (ASG). They just don't support
# this functionality

# I run it as a Lambda scheduled task so it automatically
# tags volumes of newly spun up instances for AWS 
# cost allocation.

# Variables
ec2_name_mask_to_tag = "k8s"
tags_to_add = [{
	'Key': 'Environment',
	'Value': 'k8s'}]

# Empty lists, dicts
volumes_dict = []
instances_dict = []

# AWS config
profile = boto3.Session()
ec2 = boto3.client('ec2')
response = ec2.describe_instances()
# snaposhots_response = ec2.describe_snapshots()

# Time variables
now = datetime.now()
datestring = now.strftime("%Y-%m-%d-%H-%M-%S")
# deltatime = now - timedelta(days=retention_days)


# Functions
def get_name(instance):
	for r in response['Reservations']:
		for i in r['Instances']:
			if i['InstanceId'] == instance:
				for tag in i['Tags']:
					if tag['Key'] == 'Name':
						return tag['Value']


def get_instances_dict():
	for r in response['Reservations']:
		for i in r['Instances']:
			attrib = ec2.describe_instance_attribute(Attribute='disableApiTermination', InstanceId=i['InstanceId'])
			if attrib["DisableApiTermination"]['Value'] is True:
				if i['State']['Name'] == "running":
					instances_dict.append(
						({'instance_id': i['InstanceId'], 'instance_name': get_name(i['InstanceId'])}))


def get_volumes_dict():
	for r in response['Reservations']:
		for i in r['Instances']:
			if i['State']['Name'] == "running":
				for tag in i['Tags']:
					if tag['Key'] == 'Name':
						if ec2_name_mask_to_tag in tag['Value']:
							for b in i['BlockDeviceMappings']:
								volumes_dict.append((
									{'instance_id': i['InstanceId'], 'instance_name': get_name(i['InstanceId']),
									 'device_name': b['DeviceName'], 'volume_id': b['Ebs'].get('VolumeId')}))


def add_tags():
	# add tags to volumes
	for volume in volumes_dict:
		try:
			func_response = ec2.create_tags(
				DryRun=False,
				Resources=[
					volume['volume_id'],
				],
				Tags=tags_to_add
			)
			print volume['volume_id'] + " tagged"

		except Exception as e:
			print e.message


def handler(event, context):
	get_volumes_dict()
	add_tags()
