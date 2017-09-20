#!/usr/bin/env python

# Copyright 2015: CloudCoreo Inc
# License: Apache License v2.0
# Author(s):
#   - Paul Allen (paul@cloudcoreo.com)
import boto
import boto3
import boto.ec2
import boto.ec2.autoscale
from boto.exception import EC2ResponseError
import datetime
import os
import sys
from optparse import OptionParser
from boto.vpc import VPCConnection
import subprocess
import socket
import time
from netaddr import IPNetwork

version = "0.0.1"

## globals for caching
MY_AZ = None
MY_VPC_ID = None
INSTANCE_ID = None
MY_SUBNETS = None
MY_ASG_SUBNETS = None
MY_ROUTE_TABLES = None

def parseArgs():
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("--debug",             dest="debug",          default=False, action="store_true",     help="Whether or not to run in debug mode [default: %default]")
    parser.add_option("--version",           dest="version",        default=False, action="store_true",     help="Display the version and exit")
    parser.add_option("--bip",               dest="bip",            default="",                             help="A CIDR in which all kubernetes routes will exist")
    return parser.parse_args()

def log(statement):
    statement = str(statement)
    ts = datetime.datetime.now()
    isFirst = True
    for line in statement.split("\n"):
        if isFirst:
            print("%s - %s\n" % (ts, line))
            isFirst = False
        else:
            print("%s -    %s\n" % (ts, line))

def cmd_output(args, **kwds):
    ## this function will run a command on the OS and return the result
    kwds.setdefault("stdout", subprocess.PIPE)
    kwds.setdefault("stderr", subprocess.STDOUT)
    proc = subprocess.Popen(args, **kwds)
    return proc.communicate()[0]

def metaData(dataPath):
    ## using 169.254.169.254 instead of 'instance-data' because some people
    ## like to modify their dhcp tables...
    return cmd_output(["curl", "-sL", "169.254.169.254/latest/meta-data/" + dataPath])

def getAvailabilityZone():
    ## cached
    global MY_AZ
    if MY_AZ is None:
        MY_AZ = metaData("placement/availability-zone")
    log("MY_AZ set to %s" % MY_AZ)
    return MY_AZ

def getRegion():
  myRegion = getAvailabilityZone()[:-1]
  log("region: %s" % myRegion)
  return myRegion

def getInstanceId():
    ## cached
    global INSTANCE_ID
    if INSTANCE_ID == None:
        INSTANCE_ID = metaData("instance-id")
    log("INSTANCE_ID: %s" % INSTANCE_ID)
    return INSTANCE_ID

def getSubnetById(subnetid):
    ## cached
    subnet_filters = [['subnet-id', subnetid]]
    subnet = VPC.get_all_subnets(filters=subnet_filters)[0]
    log('my subnet: %s' % subnet.id)
    return subnet

def getMyVPCId():
    global MY_VPC_ID
    if MY_VPC_ID == None:
        MY_VPC_ID = getMe().vpc_id
    log("MY_VPC_ID: %s" % MY_VPC_ID)
    return MY_VPC_ID

def getMySubnets():
    global MY_SUBNETS
    if MY_SUBNETS == None:
        az_subnet_filters = [['availability-zone', getAvailabilityZone()],['vpc-id', getMyVPCId()]]
        MY_SUBNETS = VPC.get_all_subnets(filters=az_subnet_filters)
    log("MY_SUBNETS: %s" % MY_SUBNETS)
    return MY_SUBNETS

def getMyAsgName():
    allTags = getMe().tags
    for tag in allTags:
        if 'aws:autoscaling:groupName' in tag:
            return allTags[tag]

def getMyASGSubnets():
    global MY_ASG_SUBNETS
    if MY_ASG_SUBNETS == None:
        MY_ASG_SUBNETS = []
        log(AUTOSCALE.describe_auto_scaling_groups(AutoScalingGroupNames=[getMyAsgName()]))
        myGroup = AUTOSCALE.describe_auto_scaling_groups(AutoScalingGroupNames=[getMyAsgName()])['AutoScalingGroups'][0]
        log("myGroup: %s" % myGroup['VPCZoneIdentifier'])
        for subnetId in myGroup['VPCZoneIdentifier'].split(","):

            log("  subnetId: %s" % subnetId)
            MY_ASG_SUBNETS.append(getSubnetById(subnetId))
    return MY_ASG_SUBNETS

def getMyRouteTables(subnet):
    ## this cannot be cached beacuse we need to keep checking the route tables
    rt_filters = [['vpc-id', getMyVPCId()], ['association.subnet-id', subnet.id]]
    myRouteTables = VPC.get_all_route_tables(filters=rt_filters)
    log("myRouteTables: %s" % myRouteTables)
    return myRouteTables

def getMe():
    me = EC2.get_only_instances(instance_ids=[getInstanceId()])[0]
    log("me: %s" % me)
    return me

def disableSourceDestChecks():
    EC2.modify_instance_attribute(getInstanceId(), "sourceDestCheck", False)

def main():
    log("main | creating network interface for blackhole route additions")
    for subnet in getMyASGSubnets():
        for route_table in getMyRouteTables(subnet):
            if route_table.id == None:
                continue
            routeExists = False
            for route in route_table.routes:
                if route.destination_cidr_block == options.bip:
                    routeExists = True
            if routeExists == False:
                log('adding route[%s -> %s] to table[%s]' % (options.bip, getInstanceId(), route_table.id))
                VPC.create_route(route_table_id = route_table.id,
                                 destination_cidr_block = options.bip,
                                 instance_id = getInstanceId())
            else:
                log('replacing route[%s -> %s] to table[%s]' % (options.bip, getInstanceId(), route_table.id))
                VPC.replace_route(route_table_id = route_table.id,
                                 destination_cidr_block = options.bip,
                                 instance_id = getInstanceId())

(options, args) = parseArgs()

if options.version:
    print(version)
    sys.exit(0)

EC2 = boto.ec2.connect_to_region(getRegion())
VPC = boto.vpc.connect_to_region(getRegion())
AUTOSCALE = boto3.client('autoscaling', region_name=getRegion())

disableSourceDestChecks()
main()

