#!/bin/bash

# Define variables for NS1 and NS2 names
NS1="NS1"
NS2="NS2"

# Define variables for tunnel IP addresses
NS1_TUNNEL_IP="10.10.1.2"
NS2_TUNNEL_IP="10.10.2.2"
GRE_IP_NS1="172.16.1.1/24"
GRE_IP_NS2= "172.16.1.2/24"
GRE_IP_NS1_without_mask="172.16.1.1"
GRE_IP_NS2_without_mask="172.16.1.2"

# Define variables for routed subnets
NS1_SUBNET="192.168.1.0/24"
NS2_SUBNET="192.168.2.0/24"

# Create GRE tunnel interface in NS1
sudo ip netns exec $NS1 ip tunnel add gre-tunnel mode gre local $NS1_TUNNEL_IP remote $NS2_TUNNEL_IP

# Set GRE tunnel interface up in NS1
sudo ip netns exec $NS1 ip link set gre-tunnel up

# Assign IP address to GRE tunnel interface in NS1
sudo ip netns exec $NS1 ip addr add $GRE_IP_NS1 dev gre-tunnel

# Create GRE tunnel interface in NS2
sudo ip netns exec $NS2 ip tunnel add gre-tunnel mode gre local $NS2_TUNNEL_IP remote $NS1_TUNNEL_IP

# Set GRE tunnel interface up in NS2
sudo ip netns exec $NS2 ip link set gre-tunnel up

# Assign IP address to GRE tunnel interface in NS2
sudo ip netns exec $NS2 ip addr add $GRE_IP_NS2 dev gre-tunnel

# Add route to NS1's routing table for NS2's subnet
sudo ip netns exec $NS1 ip route add $NS2_SUBNET via $GRE_IP_NS2_without_mask

# Add route to NS2's routing table for NS1's subnet
sudo ip netns exec $NS2 ip route add $NS1_SUBNET via $GRE_IP_NS1_without_mask