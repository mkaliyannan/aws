'''
AMI cleanup script.
Version - 1.0.0
Author : Mohan Kaliyannan.
Installation Steps:
pip install csv jmespath boto3 configparser itertools argparse
configure credentials under the profile ~/.aws/credentials (aws cli profile)
By default the scripts will generate the output of dryrun with 30 days.
To check arguments --help 
CSV will generate on the same location of the script. 
Don't forget to add credentials on the file.
'''
import date
import csv
import jmespath
import boto3
import configparser
from dateutil.parser import parse
import os
import time
import itertools
import datetime
import argparse

# Time String
timestr = time.strftime("%Y-%b-%d-%H-%M-%S")

# Argument parser
parser = argparse.ArgumentParser()
parser.add_argument("-y", "--release_ami",
                    help=" Get confirmation to release the AMI and associate snapshots ", action="store_true")
parser.add_argument("-d", "--days", type=int, default=30,
                    help="Please provide the number of days old. By default 30 days")
args = parser.parse_args()
# Days to delete
age = args.days

# Get list of profiles
config = configparser.ConfigParser()
path = os.path.join(os.path.expanduser('~'), '.aws/credentials')
config.read(path)
profiles = config.sections()
# print(profiles)
profile1 = profiles[0]

# Date Calculation


def days_old(date):
    get_date_obj = parse(date)
    date_obj = get_date_obj.replace(tzinfo=None)
    diff = datetime.datetime.now() - date_obj
    return diff.days


# Get list of regions
zone = []
ec2_session = boto3.Session(profile_name=profile1, region_name='us-west-1')
ec2_client = ec2_session.client('ec2')
location = ec2_client.describe_regions()
for n in location['Regions']:
    zone.append(n['RegionName'])

amiData = []
for profile in profiles:
    for region in zone:
        current_session = boto3.Session(
            profile_name=profile, region_name=region)
        client = current_session.client('ec2')
        response = client.describe_images(Owners=['self'])
        output = jmespath.search(
            "Images[].[Description,ImageId,Architecture,ImageLocation,RootDeviceType,OwnerId,CreationDate,ImageType,Name,[BlockDeviceMappings[].Ebs.SnapshotId][0][0]]", response)
        for j in output:
            a = [[j[0], j[0], j[1], j[2], j[3], j[4], j[5],
                  j[6], j[7], j[8], j[9], region, profile]]
            amiData.append(a)

retAmi = []
dryAmi = []
for i in amiData:
    for i in i:
        day_old = days_old(i[-6])
        read_date = i[-6]
        read_date = read_date[:-14]
        ami_id = i[2]
        snapshot = i[-3]
        # print(i)
        if day_old > age:
            if args.release_ami is True:
                z = [[day_old, ami_id, snapshot, read_date, i[-7], i[-2]]]
                retAmi.append(z)
                print("Deleting -->Daysold:{},AMIID:{},Snapshot:{},Created:{},Region:{},AccountID:{}".format(
                    day_old, ami_id, snapshot, read_date, i[-2], i[-7]))
                ami_session = boto3.Session(
                    profile_name=i[-1], region_name=i[-2])
                client = ami_session.client('ec2')
                client.deregister_image(ImageId=ami_id)
                client.delete_snapshot(SnapshotId=snapshot)

            else:
                y = [[day_old, ami_id, snapshot, read_date, i[-7], i[-2]]]
                dryAmi.append(y)
                print("DryRun ==> Daysold:{},AMIID:{},Snapshot:{},Created:{},Region:{},AccountID:{}".format(
                    day_old, ami_id, snapshot, read_date, i[-2], i[-7]))

# Write Volume Data to CSV file with headers
x = list(itertools.chain(*retAmi))
y = list(itertools.chain(*dryAmi))


if args.release_ami is True:
    with open(timestr+"-DeletedAmi.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(['Retire Days', 'Deleted-AMI ID', 'Deleted-AMI Snapshots',
                        'Date of Created', 'Account ID', 'AMI Region'])
        writer.writerows(x)
else:
    with open(timestr+"-DryAmi.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(['Retire Days', 'AMI ID', 'AMI Snapshots',
                        'Date of Created', 'Account ID', 'AMI Region'])
        writer.writerows(y)
