#!/bin/bash

# Define namespace names
NS1="NS1"
NS2="NS2"

# Define network interface names
NS1_NET1_VETH0="NS1_Net1_veth0"
NS2_NET1_VETH0="NS2_Net1_veth0"

# Define VXLAN parameters
VXLAN_ID=20
VXLAN_DST_PORT=4789

# Configure VXLAN on NS2
sudo ip netns exec $NS2 ip link add vxlan1 type vxlan id $VXLAN_ID dstport $VXLAN_DST_PORT local 10.10.2.2 remote 10.10.1.2
sudo ip netns exec $NS2 ip link set vxlan1 up
sudo ip netns exec $NS2 brctl addbr BR_vxlan
sudo ip netns exec $NS2 ip link set BR_vxlan up
sudo ip netns exec $NS2 brctl addif BR_vxlan vxlan1
sudo ip netns exec $NS2 ip addr del 192.168.20.1/24 dev $NS1_NET1_VETH0
sudo ip netns exec $NS2 brctl addif BR_vxlan $NS2_NET1_VETH0

# Configure VXLAN on NS1
sudo ip netns exec $NS1 ip link add vxlan1 type vxlan id $VXLAN_ID dstport $VXLAN_DST_PORT local 10.10.1.2 remote 10.10.2.2
sudo ip netns exec $NS1 ip link set vxlan1 up
sudo ip netns exec $NS1 brctl addbr BR_vxlan
sudo ip netns exec $NS1 ip link set BR_vxlan up
sudo ip netns exec $NS1 brctl addif BR_vxlan vxlan1
sudo ip netns exec $NS1 ip addr del 192.168.10.1/24 dev $NS1_NET1_VETH0
sudo ip netns exec $NS1 brctl addif BR_vxlan $NS1_NET1_VETH0
