#!/bin/bash

# Define variables for NS1 and NS2 names
NS1="NS1"
NS2="NS2"
GRE_IP_NS1_without_mask="172.16.1.1"
GRE_IP_NS2_without_mask="172.16.1.2"

# Define variables for routed subnets
NS1_SUBNET="192.168.1.0/24"
NS2_SUBNET="192.168.2.0/24"

# Delete GRE tunnel interface in NS1
sudo ip netns exec $NS1 ip link delete gre-tunnel

# Delete GRE tunnel interface in NS2
sudo ip netns exec $NS2 ip link delete gre-tunnel

# Delete routes from NS1's routing table for NS2's subnet
sudo ip netns exec $NS1 ip route del $NS2_SUBNET via $GRE_IP_NS2_without_mask

# Delete routes from NS2's routing table for NS1's subnet
sudo ip netns exec $NS2 ip route del $NS1_SUBNET via $GRE_IP_NS1_without_mask
