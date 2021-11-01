
'''
Get the S3 buckets data size and location with account no.
Author: Mohan Kaliyannan.
Version : 1.0.0
Installation: pip install csv jmespath boto3 itertools configparser bitmath
Excute : python3 Get-S3-Details.py
CSV will be on the generate on the same location where scripts reside.
'''


import csv
import jmespath
import boto3
import itertools
import configparser
import os
from datetime import datetime
from bitmath import *
import time


# Time String
timestr = time.strftime("%Y-%b-%d-%H-%M-%S")


# Get list of profiles
config = configparser.ConfigParser()
path = os.path.join(os.path.expanduser('~'), '.aws/credentials')
config.read(path)
profiles = config.sections()
profile1 = profiles[0]


# Get list of regions
zone = []
y=0
s3List=[]
session = boto3.Session(profile_name=profile1)
ec2_client = session.client('ec2', region_name="us-west-1")
location = ec2_client.describe_regions()
for n in location['Regions']:
    zone.append(n['RegionName'])
for profile in profiles:
            # Get Account
            session = boto3.Session(profile_name=profile)
            s3 = session.client('s3')
            stsclient = session.client('sts')
            # S3 buckets
            response = s3.list_buckets()
            output=jmespath.search("Buckets[].[Name,CreationDate]",response)
         
            for x in output:
                #print(x[0])
                location = s3.get_bucket_location(Bucket=x[0])
                region = jmespath.search("LocationConstraint", location)
                stsregion = stsclient.get_caller_identity()
                soutput = jmespath.search("Account", stsregion)
                s3ctime=x[1].strftime("%Y-%m-%d %H:%M:%S+%z")
                s3ctime=s3ctime[:-14]
                size = 0
                            
                               

            for x in output:
                y=y+1
                obj = s3.list_objects(Bucket=x[0])
                if "Contents" in obj:
                    for b in obj["Contents"]:
                       size += b["Size"]
                else:
                    size=0
                a=int(Byte(size).to_GiB())
                
                x=[[str(y),x[0],region,soutput,s3ctime,str(a)]]
                s3List.append(x)

x = list(itertools.chain(*s3List))
with open(timestr+"-S3.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(['S.No','Bucket Name', 'Region', 'AccountID',
                    'Created Date', 'Size in GB'])
    writer.writerows(x)
