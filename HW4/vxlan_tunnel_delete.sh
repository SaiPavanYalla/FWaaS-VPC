#!/bin/bash

# Variables for NS1
NS1="NS1"                              
NS1_INTERFACE="NS1_Net1_veth0"        
NS1_INTERFACE_IP="192.168.1.1/24"     
NS1_VXLAN="vxlan1"                     
NS1_VXLAN_ID="20"                      
NS1_BR_VXLAN="BR_vxlan"                
NS1_LOCAL_IP="10.10.1.2"               
NS1_REMOTE_IP="10.10.2.2"              

# Variables for NS2
NS2="NS2"                              
NS2_INTERFACE="NS2_Net1_veth0"         
NS2_INTERFACE_IP="192.168.1.1/24"     
NS2_VXLAN="vxlan1"                     
NS2_VXLAN_ID="20"                      
NS2_BR_VXLAN="BR_vxlan"                
NS2_LOCAL_IP="10.10.2.2"               
NS2_REMOTE_IP="10.10.1.2"              

# Delete VXLAN configuration on NS2
sudo ip netns exec $NS2 brctl delif $NS2_BR_VXLAN $NS2_INTERFACE
sudo ip netns exec $NS2 ip link set $NS2_BR_VXLAN down
sudo ip netns exec $NS2 brctl delbr $NS2_BR_VXLAN
sudo ip netns exec $NS2 ip link set $NS2_VXLAN down
sudo ip netns exec $NS2 ip link del $NS2_VXLAN

# Delete VXLAN configuration on NS1
sudo ip netns exec $NS1 brctl delif $NS1_BR_VXLAN $NS1_INTERFACE
sudo ip netns exec $NS1 ip link set $NS1_BR_VXLAN down
sudo ip netns exec $NS1 brctl delbr $NS1_BR_VXLAN
sudo ip netns exec $NS1 ip link set $NS1_VXLAN down
sudo ip netns exec $NS1 ip link del $NS1_VXLAN
