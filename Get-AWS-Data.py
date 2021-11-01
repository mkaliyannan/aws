import csv
import jmespath
import boto3
import itertools
import configparser
import os
import time
import pandas as pd

# EBS Volumes
# EC2 Instances
# EIP
# AMI Volumes
# Time String
timestr = time.strftime("%Y-%b-%d-%H-%M-%S")

# Get list of profiles
config = configparser.ConfigParser()
path = os.path.join(os.path.expanduser('~'), '.aws/credentials')
config.read(path)
profiles = config.sections()
# print(profiles)
profile1 = profiles[0]

# Get list of regions
zone = []
ec2_session = boto3.Session(profile_name=profile1, region_name='us-west-1')
ec2_client = ec2_session.client('ec2')
location = ec2_client.describe_regions()
for n in location['Regions']:
    zone.append(n['RegionName'])


# # Get list of EC2 attributes from all profiles and regions
Ec2Vol = []
for profile in profiles:
    for region in zone:
        current_session = boto3.Session(
            profile_name=profile, region_name=region)
        stsclient = current_session.client('sts')
        stsregion = stsclient.get_caller_identity()
        stsout = jmespath.search("Account", stsregion)
        client = current_session.client('ec2')
        response = client.describe_volumes()
        output = jmespath.search(
            "Volumes[*].[VolumeId,AvailabilityZone,Size,State,Attachments[0].State,Attachments[0].InstanceId,Iops,Tags[0].Value,VolumeType]", response)
        for x in output:
            x = [[x[0], x[1], str(x[2]), x[3], x[4], x[5], str(
                x[6]), x[7], x[8], str(stsout)]]
            Ec2Vol.append(x)

# Get list of EC2 attributes from all profiles and regions
Ec2Data = []
for profile in profiles:
    for region in zone:
        current_session = boto3.Session(
            profile_name=profile, region_name=region)
        client = current_session.client('ec2')
        response = client.describe_instances()
        output = jmespath.search("Reservations[].Instances[].[NetworkInterfaces[0].OwnerId,ImageId,InstanceId, InstanceType, \
            State.Name, Placement.AvailabilityZone, PrivateIpAddress, PublicIpAddress, KeyName, [Tags[?Key=='Name'].Value] [0][0]]", response)
        Ec2Data.append(output)

amiData = []
for profile in profiles:
    for region in zone:
        current_session = boto3.Session(
            profile_name=profile, region_name=region)
        client = current_session.client('ec2')
        response = client.describe_images(Owners=['self'])
        output = jmespath.search(
            "Images[].[VirtualizationType,Description,PlatformDetails,EnaSupport,Hypervisor,State,SriovNetSupport,ImageId,UsageOperation,Architecture,ImageLocation,RootDeviceType,OwnerId,RootDeviceName,CreationDate,Public,ImageType,Name]", response)
        amiData.append(output)


EipUsed = []
EipNused = []
x = 0
for profile in profiles:
    for region in zone:

        current_session = boto3.Session(
            profile_name=profile, region_name=region)
        client = current_session.client('ec2')
        stsclient = current_session.client('sts')
        response = client.describe_addresses()
        # response1= client.describe_addresses()
        output = jmespath.search(
            "Addresses[].[PublicIp,NetworkInterfaceOwnerId,PrivateIpAddress,NetworkBorderGroup]", response)
        stsregion = stsclient.get_caller_identity()
        stsout = jmespath.search("Account", stsregion)
        # print(response['Addresses'])
        for address in output:
            x = x+1
            if address[1] is None:
                a = [[ address[0], address[3], stsout]]
                EipNused.append(a)
            else:
                a = [[ address[0], address[3], stsout]]
                EipUsed.append(a)


# Write myData to CSV file with headers
x = list(itertools.chain(*Ec2Data))
with open(timestr+"-ec2-inventory.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(['AccountID', 'AMI ID', 'InstanceID', 'Type', 'State',
                    'AZ', 'PrivateIP', 'PublicIP', 'KeyPair', 'Name'])
    writer.writerows(x)

# Write amiData to CSV file with headers
y = list(itertools.chain(*amiData))
with open(timestr+"-ami-inventory.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(['VirtualizationType', 'Description', 'PlatformDetails', 'EnaSupport', 'Hypervisor', 'State', 'SriovNetSupport', 'ImageId',
                    'UsageOperation', 'Architecture', 'ImageLocation', 'RootDeviceType', 'OwnerId', 'RootDeviceName', 'CreationDate', 'Public', 'ImageType', 'Name'])
    writer.writerows(y)

# Write Volume Data to CSV file with headers
vol = list(itertools.chain(*Ec2Vol))
with open(timestr+"-EBS-inventory.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(['VolumeId', 'AvailabilityZone', 'Size', 'State',
                    'Volume State', 'Attached InstanceId', 'Disk IOPS', 'Tags', 'Disk Type', 'Account No'])
    writer.writerows(vol)
# Write Volume Data to CSV file with headers
x = list(itertools.chain(*EipNused))
y = list(itertools.chain(*EipUsed))

with open(timestr+"-EIP-notused.csv", "w", newline="") as f:
    writer=csv.writer(f)
    writer.writerow(['IPAddress','Region','Account ID'])
    writer.writerows(x)
  
with open(timestr+"-EIP-used.csv", "w", newline="") as f:
    writer=csv.writer(f)
    writer.writerow(['IPAddress','Region','Account ID'])
    writer.writerows(y)
