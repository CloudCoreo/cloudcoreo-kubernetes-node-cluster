cloudcoreo-kubernetes-node-cluster
===================================



## Description
This repository is the [CloudCoreo](https://www.cloudcoreo.com) stack for kubernetes node clusters.

This stack will add a scalable, highly availabe, self healing kubernetes node cluster based on the [CloudCoreo leader election cluster here](http://hub.cloudcoreo.com/stack/leader-elect-cluster&#95;35519).

Kubernetes allows you to manage a cluster of Linux containers as a single system to accelerate Dev and simplify Ops. The architecture is such that master and node clusters are both required. This is only the cluster for the nodes and expects a master cluster available [here](http://hub.cloudcoreo.com/stack/cloudcoreo-kubernetes-master-cluster&#95;39a3c).

The node cluster is quite interesting in the way it works with the master cluster. There is a bit of work necessary in order to get routing working. Each node must have its own route entry in the route tables for the VPC in which it is containted. As a user of this cluster, you must specify the master service cidr, but you must ALSO specify the cidr block size which will be used to subdivide the master range amongst the nodes.

For instance:

Lets assume you set the `KUBE&#95;NODE&#95;SERVICE&#95;IP&#95;CIDRS` variable to `10.234.0.0/20`. 
Your job is to decide how many (maximum) containers you want to run simultaneously on each node. 
For this, lets decide on `62` as the maximum. Great! That just happens to mean you put in a value for `KUBE&#95;NODE&#95;SERVICE&#95;IP&#95;CIDRS&#95;SUBDIVIDER` that gets you 64 addresses (62 usable, 1 for the broadcast and one for network address). That value is `26`.

```
KUBE&#95;NODE&#95;SERVICE&#95;IP&#95;CIDRS = 10.234.0.0/20
KUBE&#95;NODE&#95;SERVICE&#95;IP&#95;CIDRS&#95;SUBDIVIDER = 25
```

So what happens now?

As nodes come up they create a table of usable values based on the two variables above. In our case there are 32 possible cidrs:
```
10.234.0.0/26
10.234.0.64/26
10.234.1.0/26
10.234.1.64/26
10.234.2.0/26
10.234.2.64/26
...
...
10.234.13.0/26
10.234.13.64/26
10.234.14.0/26
10.234.14.64/26
10.234.15.0/26
10.234.15.64/26
```
Each node will check the kubernets nodes via kubectl command and find an unused network block. It will then insert itself into the proper routing tables. The 'used network blocks' are determined by the labels set on the nodes.



## Hierarchy
![composite inheritance hierarchy](https://raw.githubusercontent.com/CloudCoreo/cloudcoreo-kubernetes-node-cluster/master/images/hierarchy.png "composite inheritance hierarchy")



## Required variables with no default

### `KUBE_CLUSTER_AMI`:
  * description: the ami to launch for the cluster - default is Amazon Linux AMI 2015.03 (HVM), SSD Volume Type


## Required variables with default

### `KUBE_VERSION`:
  * description: kubernetes version
  * default: 1.1.4

### `VPC_NAME`:
  * description: the name of the VPC
  * default: kube-dev


### `VPC_CIDR`:
  * description: the cloudcoreo defined vpc to add this cluster to
  * default: 10.1.0.0/16

### `PRIVATE_SUBNET_NAME`:
  * description: the cloudcoreo name of the private vpc subnets. eg private-us-west-2c
  * default: kube-dev-private-us-west-1

### `PRIVATE_ROUTE_NAME`:
  * description: the private subnet in which the cluster should be added
  * default: dev-private-route

### `DNS_ZONE`:
  * description: the zone in which the internal elb dns entry should be maintained
  * default: dev.aws.lcloud.com

### `KUBE_NODE_IP_CIDRS`:
  * description: Node IP CIDR block - NOTE - This MUST be different that the cidr specified for the kubernetes master service cidrs
  * default: 10.2.1.0/24


### `KUBE_NODE_IP_CIDRS_SUBDIVIDER`:
  * description: kubernetes service cidrs
  * default: 26

### `KUBE_MASTER_NAME`:
  * description: the name of the cluster - this will become your dns record too
  * default: kube-master

### `KUBE_NODE_NAME`:
  * description: the name of the cluster - this will become your dns record too
  * default: kube-node

### `KUBE_NODE_TCP_HEALTH_CHECK_PORT`:
  * description: a tcp port the ELB will check every so often - this defines health and ASG termination
  * default: 10250

### `KUBE_NODE_INSTANCE_TRAFFIC_PORTS`:
  * description: ports to allow traffic on directly to the instances
  * default: 1..65535

### `KUBE_NODE_INSTANCE_TRAFFIC_CIDRS`:
  * description: cidrs that are allowed to access the instances directly
  * default: 10.0.0.0/8

### `KUBE_NODE_SIZE`:
  * description: the image size to launch
  * default: t2.small


### `KUBE_NODE_GROUP_SIZE_MIN`:
  * description: the minimum number of instances to launch
  * default: 3

### `KUBE_NODE_GROUP_SIZE_MAX`:
  * description: the maxmium number of instances to launch
  * default: 6

### `KUBE_NODE_HEALTH_CHECK_GRACE_PERIOD`:
  * description: the time in seconds to allow for instance to boot before checking health
  * default: 600

### `KUBE_NODE_UPGRADE_COOLDOWN`:
  * description: the time in seconds between rolling instances during an upgrade
  * default: 300

### `TIMEZONE`:
  * description: the timezone the servers should come up in
  * default: America/LosAngeles


### `KUBE_NODE_KEY`:
  * description: the ssh key to associate with the instance(s) - blank will disable ssh
  * default: cloudops


## Optional variables with default

### `KUBE_PROXY_LOG_FILE`:
  * description: kube proxy log file
  * default: /var/log/kube-proxy.log


### `KUBE_KUBLET_LOG_FILE`:
  * description: kublet log file
  * default: /var/log/kube-kublet.log


### `KUBE_NODE_ELB_LISTENERS`:
  * description: ports to pass through the elb to the kubernetes node cluster instances
  * default: 
```
[
  {
      :elb_protocol => 'tcp',
      :elb_port => 10250,
      :to_protocol => 'tcp',
      :to_port => 10250
  }
]

```


## Optional variables with no default

### `VPC_SEARCH_TAGS`:
  * description: if you have more than one VPC with the same CIDR, and it is not under CloudCoreo control, we need a way to find it. Enter some unique tags that exist on the VPC you want us to find. ['env=production','Name=prod-vpc']

### `PRIVATE_ROUTE_SEARCH_TAGS`:
  * description: if you more than one route table or set of route tables, and it is not under CloudCoreo control, we need a way to find it. Enter some unique tags that exist on your route tables you want us to find. i.e. ['Name=my-private-routetable','env=dev']

### `PRIVATE_SUBNET_SEARCH_TAGS`:
  * description: Usually the private-routetable association is enough for us to find the subnets you need, but if you have more than one subnet, we may need a way to find them. unique tags is a great way. enter them there. i.e. ['Name=my-private-subnet']

### `KUBE_NODE_ELB_TRAFFIC_PORTS`:
  * description: leave this blank - we are using ELB for health checks only

### `KUBE_NODE_ELB_TRAFFIC_CIDRS`:
  * description: leave this blank - we are using ELB for health checks only

## Tags
1. Container Management
1. Google
1. Kubernetes
1. High Availability
1. Master
1. Cluster

## Categories
1. Servers



## Diagram
![diagram](https://raw.githubusercontent.com/CloudCoreo/cloudcoreo-kubernetes-node-cluster/master/images/diagram.png "diagram")


## Icon


