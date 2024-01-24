'''
* Steps to create automatation under ( ~/.aws/credentials)
* Add the credentials to .aws_crendentails
* For dryrun execute as it is
* For actionrelease the address please remove the comment on the line no 86.
* Add this script to crontab to schedule the prefer duration
'''
import date
import csv
import jmespath
import boto3
import itertools
import configparser
import os
import pandas as pd
from numpy.lib.function_base import append
import time
import argparse


# Time String
timestr = time.strftime("%Y-%b-%d-%H-%M-%S")
# Argument parser
parser = argparse.ArgumentParser()
parser.add_argument("-y", "--kickout_eip",
                    help="Add an argument -y to release EIP addresses", action="store_true")
args = parser.parse_args()

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
        output = jmespath.search(
            "Addresses[].[PublicIp,NetworkInterfaceOwnerId,PrivateIpAddress,NetworkBorderGroup,AllocationId]", response)
        stsregion = stsclient.get_caller_identity()
        stsout = jmespath.search("Account", stsregion)
        # print(response['Addresses']).
        for address in output:
            x = x+1
            if address[1] is None:
                a = [[address[0], address[3], stsout, address[-1],profile]]
                EipNused.append(a)
            else:
                a = [[address[0], address[3], stsout]]
                EipUsed.append(a)

# Write Volume Data to CSV file with headers
x = list(itertools.chain(*EipNused))
y = list(itertools.chain(*EipUsed))

with open(timestr+"-EIP-notused.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(['IPAddress', 'Region', 'Account ID'])
    writer.writerows(x)

with open(timestr+"-EIP-used.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(['IPAddress', 'Region', 'Account ID'])
    writer.writerows(y)

for i in EipNused:
    for i in i:
        if args.kickout_eip is True:
            print("The following IP address will be release :{}\n".format(i[0]))
            # For action uncomment below line:87
            eip_region = boto3.Session( profile_name=i[-1], region_name=i[1])
            client = eip_region.client('ec2')
            release = client.release_address(AllocationId=i[3])
           # print(release)
        else:
            print(" EIP will not release until you pass argument  -y : {}".format(i[0]))
