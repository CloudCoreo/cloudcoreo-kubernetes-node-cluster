This repository is the [CloudCoreo](https://www.cloudcoreo.com) stack for kubernetes node clusters.

This stack will add a scalable, highly availabe, self healing kubernetes node cluster based on the [CloudCoreo leader election cluster here](http://hub.cloudcoreo.com/stack/leader-elect-cluster_35519).

Kubernetes allows you to manage a cluster of Linux containers as a single system to accelerate Dev and simplify Ops. The architecture is such that master and node clusters are both required. This is only the cluster for the nodes and expects a master cluster available [here](http://hub.cloudcoreo.com/stack/cloudcoreo-kubernetes-master-cluster_39a3c).

The node cluster is quite interesting in the way it works with the master cluster. There is a bit of work necessary in order to get routing working. Each node must have its own route entry in the route tables for the VPC in which it is containted. As a user of this cluster, you must specify the master service cidr, but you must ALSO specify the cidr block size which will be used to subdivide the master range amongst the nodes.

For instance:

Lets assume you set the `KUBE_NODE_SERVICE_IP_CIDRS` variable to `10.234.0.0/20`. 
Your job is to decide how many (maximum) containers you want to run simultaneously on each node. 
For this, lets decide on `62` as the maximum. Great! That just happens to mean you put in a value for `KUBE_NODE_SERVICE_IP_CIDRS_SUBDIVIDER` that gets you 64 addresses (62 usable, 1 for the broadcast and one for network address). That value is `26`.

```
KUBE_NODE_SERVICE_IP_CIDRS = 10.234.0.0/20
KUBE_NODE_SERVICE_IP_CIDRS_SUBDIVIDER = 25
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

