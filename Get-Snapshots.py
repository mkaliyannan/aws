'''
Version : 1.0.0
Credentials : it will get the credentials from aws profile. 
Multiple profile: add muliple accesskey,with profile name. refer aws documentation for aws_profile.
Region: It will look all regions within the account by default.
For help: python3 Get-Snapshots.py --help
Dryrun : python3 Get-Snapshots.py
No of Days: python3 -d 1500. ie: 1500 is 1500 days. by default will set to 30 days.
Delete action : python3 -d 1500 -y ie: -y will delete the snapshots older than specific daye.

'''
import boto3
from botocore.exceptions import ClientError
import jmespath
import configparser
import os
import time
import datetime as d
from time import sleep
import argparse

# Argument parser
parser = argparse.ArgumentParser()
parser.add_argument("-y", "--remove_snapshots",
                    help=" Passing this argument will delete the snapshots and will not reversibe. execute with extra caution ", default=True, action="store_true")
parser.add_argument("-d", "--days", type=int, default=30,
                    help="Please enter the days to get results. By default 30 days")
args = parser.parse_args()

DRYRUN = args.remove_snapshots 
MAX_DAYS_TO_RETAIN = args.days 

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
timestr = time.strftime("%Y-%b-%d-%H-%M-%S")
for profile in profiles:
    for region in zone:
       #current_session = boto3.setup_default_session(profile_name=profile, region_name=region)

        current_session = boto3.Session(profile_name=profile, region_name=region)
        stsclient = current_session.client('sts')
        stsregion = stsclient.get_caller_identity()
        stsout = jmespath.search("Account", stsregion)
        ec2 = current_session.client('ec2')
        print(stsout,region)
        # # print(timestr)
        snapshots = ec2.describe_snapshots(OwnerIds=['self'])

        snapshots_deleted = 0
        snapshots_retained = 0
        today = d.datetime.today()
        for snapshot in snapshots['Snapshots']:
            difference = today - snapshot['StartTime'].replace(tzinfo=None)
            if difference.days > MAX_DAYS_TO_RETAIN:
                print(MAX_DAYS_TO_RETAIN)
                print("deleting this snapshot: {} - {}".format(difference.days, snapshot['SnapshotId']))
                snapshots_deleted = snapshots_deleted + 1
                try:
                    sleep(0.005) # in order to avoid AWS API rate limiting exception
                    ec2.delete_snapshot(SnapshotId=snapshot['SnapshotId'], DryRun=DRYRUN)
                except Exception as e:
                    print("{}".format(str(e)))
                    break
            else:
                print("retaining this snapshot: {} - {}".format(difference.days, snapshot['SnapshotId']))
                snapshots_retained = snapshots_retained + 1

        print("Total snapshots: {}".format(len(snapshots['Snapshots'])))
        print("Snapshots deleted: {}".format(snapshots_deleted))
        print("Snapshots preserved: {}".format(snapshots_retained))