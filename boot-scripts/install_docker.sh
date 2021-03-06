#!/bin/bash
set -x

yum install -y docker
pip install netaddr

source /etc/profile.d/cluster

all_nets="$(python ./lib/generate_network_blocks.py  --master-cidr-block ${KUBE_NODE_IP_CIDRS} --cidr-divider ${KUBE_NODE_IP_CIDRS_SUBDIVIDER})"
num_nets="$(echo $all_nets | awk '{print NF}')"
asg_addresses=$(echo "$CLUSTER_ADDRESSES , $MY_IPADDRESS" | perl -pe 's{,}{}g; s{ }{\n}g' | sort -t . -k 1,1n -k 2,2n -k 3,3n -k 4,4n)
num_members="$(echo $asg_addresses | awk '{print NF}')"

my_location_in_list=0
for ip in $asg_addresses; do
    if [ "$ip" = "$MY_IPADDRESS" ]; then
        break;
    fi
    my_location_in_list=$((my_location_in_list + 1))
done

## get an unused bip
(
    kube_dir="/opt/kubernetes"
    cd "$kube_dir"
    used_nets="$(./kubectl --server=http://${KUBE_MASTER_NAME}.${DNS_ZONE}:8080 get nodes --show-labels=true | grep -i \\bready\\b | grep ipblock | awk -F'ipblock=' '{print $2}' | perl -pe 's#([0-9\.]+).*#\1#g')"

    DOCKER_BIP=
    net_counter=1
    while [ $num_members -gt 0 ]; do
        for aNet in $all_nets; do
            if [ $((net_counter%num_members)) = $my_location_in_list ]; then
                unused=true
                for uNet in $used_nets; do
                    if [ "$uNet" = "$aNet" ]; then
                        unused=false
                    fi
                done

                if [ $unused = true ]; then
                    DOCKER_BIP="$aNet"
                    break
                fi
            fi
            net_counter=$((net_counter + 1))
        done
        if [ "${DOCKER_BIP:-}" = "" -a "$num_members" = "0" ]; then
            echo "no more net space open - exiting"
            exit 1
        fi
        if [ "${DOCKER_BIP:-}" != "" ]; then
            break;
        fi
        num_members=$((num_members - 1))
    done
    ## lets add 1 to the net                                                                                                                                                                                                                                                                                                                                                
    baseaddr="$(echo $DOCKER_BIP | cut -d. -f1-3)"
    lsv="$(echo $DOCKER_BIP | cut -d. -f4)"
    docker_bind="$baseaddr.$((lsv + 1))"
    mkdir -p /etc/docker
    cat <<EOF > /etc/docker/daemon.json
{
  "storage-driver": "devicemapper"
}
EOF
    ## docker config  
    cat <<EOF > /etc/sysconfig/docker
# The max number of open files for the daemon itself, and all
# running containers.  The default value of 1048576 mirrors the value
# used by the systemd service unit.
DAEMON_MAXFILES=1048576

# Additional startup options for the Docker daemon, for example:
# OPTIONS="--ip-forward=true --iptables=true"
# By default we limit the number of open files per container
# dockernet=${DOCKER_BIP}/${KUBE_NODE_IP_CIDRS_SUBDIVIDER}
OPTIONS="--default-ulimit nofile=1024:4096 --bip=${docker_bind}/${KUBE_NODE_IP_CIDRS_SUBDIVIDER}"
EOF

)
