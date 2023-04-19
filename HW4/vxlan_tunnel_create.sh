#!/bin/bash

# Variables for NS1
NS1="NS1"                              # Define variable for network namespace 1
NS1_INTERFACE="NS1_Net1_veth0"        # Define variable for interface of namespace 1 gateway 
NS1_INTERFACE_IP="192.168.1.1/24"     # Define variable for ip of namespace 1 gateway 
NS1_VXLAN="vxlan1"                     # Define variable for vxlan interface of namespace 1
NS1_VXLAN_ID="20"                      # Define variable for vxlan ID of namespace 1
NS1_BR_VXLAN="BR_vxlan"                # Define variable for bridge of namespace 1 and vxlan 1
NS1_LOCAL_IP="10.10.1.2"               # Define variable for local IP address of namespace 1
NS1_REMOTE_IP="10.10.2.2"              # Define variable for remote IP address of namespace 1


# Variables for NS2
NS2="NS2"                              # Define variable for network namespace 2
NS2_INTERFACE="NS2_Net1_veth0"         # Define variable for interface of namespace 2 gateway 
NS2_INTERFACE_IP="192.168.1.1/24"     # Define variable for ip of namespace 2 gateway 
NS2_VXLAN="vxlan1"                     # Define variable for vxlan interface of namespace 2
NS2_VXLAN_ID="20"                      # Define variable for vxlan ID of namespace 2
NS2_BR_VXLAN="BR_vxlan"                # Define variable for bridge of namespace 2 and vxlan 1
NS2_LOCAL_IP="10.10.2.2"               # Define variable for local IP address of namespace 2
NS2_REMOTE_IP="10.10.1.2"              # Define variable for remote IP address of namespace 2

# Configure VXLAN on NS2
sudo ip netns exec $NS2 ip link add $NS2_VXLAN type vxlan id $NS2_VXLAN_ID dstport 4789 local $NS2_LOCAL_IP remote $NS2_REMOTE_IP     # Add VXLAN interface to namespace 2 with specified ID, remote and local IP addresses
sudo ip netns exec $NS2 ip link set $NS2_VXLAN up                   # Set VXLAN interface up
sudo ip netns exec $NS2 brctl addbr $NS2_BR_VXLAN                   # Add bridge  to namespace 2
sudo ip netns exec $NS2 ip link set $NS2_BR_VXLAN up                # Set bridge interface up
sudo ip netns exec $NS2 brctl addif $NS2_BR_VXLAN $NS2_VXLAN         # Add VXLAN interface to bridge 
sudo ip netns exec $NS2 ip addr del $NS2_INTERFACE_IP dev $NS2_NET1_VETH0    # Delete IP address from default gateway interface of namespace 2
sudo ip netns exec $NS2 brctl addif $NS2_BR_VXLAN $NS2_NET1_VETH0    # Add default gateway interface of namespace 2 to bridge 

# Configure VXLAN on NS1
sudo ip netns exec $NS1 ip link add $NS1_VXLAN type vxlan id $NS1_VXLAN_ID dstport 4789 local $NS1_LOCAL_IP remote $NS1_REMOTE_IP     # Add VXLAN interface to namespace 1 with specified ID, remote and local IP addresses
sudo ip netns exec $NS1 ip link set $NS1_VXLAN up                   # Set VXLAN interface up
udo ip netns exec $NS1 brctl addbr $NS1_BR_VXLAN                   # Add bridge to namespace 1
sudo ip netns exec $NS1 ip link set $NS1_BR_VXLAN up                # Set bridge interface up
sudo ip netns exec $NS1 brctl addif $NS1_BR_VXLAN $NS1_VXLAN         # Add VXLAN interface to bridge 
sudo ip netns exec $NS1 ip addr del $NS1_INTERFACE_IP dev $NS1_INTERFACE   # Delete IP address from default gateway
sudo ip netns exec $NS1 brctl addif $NS1_BR_VXLAN $NS1_INTERFACE    # Add default gateway interface of namespace 1 to bridge

