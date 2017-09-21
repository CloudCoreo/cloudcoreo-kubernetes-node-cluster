#!/bin/bash
set -x
######################################################################
#
# VARIABLES:
#   KUBE_VERSION = 1.0.6
#   KUBE_MASTER_NAME =
#   DNS_ZONE = dev.aws.lcloud.com
#   KUBE_KUBLET_LOG_FILE = /var/log/kube-kublet.log
#   KUBE_PROXY_LOG_FILE = /var/log/kube-proxy.log
#
# PORTS:
#     kublet = 10248, 10250, 10255
#######################################################################

## this stack extends the leader elect cluster, so lets source in the cluster profile and expose some variables to us
source /etc/profile.d/cluster

kube_dir="/opt/kubernetes"
sup_conf="/etc/supervisord.conf"
(
    cd "$kube_dir"

    name="$(echo $MY_IPADDRESS | perl -pe 's{\.}{}g')"
    name="$MY_IPADDRESS"

    cat <<EOF >> "$sup_conf"

[program:kube-proxy]
redirect_stderr=true
stdout_logfile=${KUBE_PROXY_LOG_FILE}
stdout_logfile_maxbytes=50MB
command=/bin/bash -c '$kube_dir/kube-proxy \\
                        --v=2 \\
                        --master="http://${KUBE_MASTER_NAME}.${DNS_ZONE}:8080" \\
                        '

[program:kublet]
redirect_stderr=true
stdout_logfile=${KUBE_KUBLET_LOG_FILE}
stdout_logfile_maxbytes=50MB
command=/bin/bash -c '$kube_dir/kubelet \\
                        --v=2 \\
                        --address=$MY_IPADDRESS \\
                        --api_servers=http://${KUBE_MASTER_NAME}.${DNS_ZONE}:8080 \\
                        --hostname_override=$name \\
                        --port=10250 \\
                        '

EOF
    /etc/init.d/supervisord restart
)
