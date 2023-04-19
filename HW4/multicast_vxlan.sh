sudo ip netns exec NS1 ip link add vxlan0 type vxlan id 10 group 239.0.0.1 dev NST_NS1_veth1  dstport 4789 local 10.10.1.2
sudo ip netns exec NS2 ip link add vxlan0 type vxlan id 10 group 239.0.0.1 dev NST_NS2_veth1  dstport 4789 local 10.10.2.2
sudo ip netns exec NS3 ip link add vxlan0 type vxlan id 10 group 239.0.0.1 dev NST_NS3_veth1  dstport 4789 local 10.10.3.2

sudo ip netns exec NS1 brctl addbr BR_vxlan0
sudo ip netns exec NS1 ip link set vxlan0 up
sudo ip netns exec NS1 ip link set BR_vxlan0 up
sudo ip netns exec NS1 brctl addif BR_vxlan0 vxlan0
sudo ip netns exec NS1 brctl addif BR_vxlan0 NS1_Net1_veth0   

sudo ip netns exec NS2 brctl addbr BR_vxlan0
sudo ip netns exec NS2 ip link set vxlan0 up
sudo ip netns exec NS2 ip link set BR_vxlan0 up
sudo ip netns exec NS2 brctl addif BR_vxlan0 vxlan0
sudo ip netns exec NS2 brctl addif BR_vxlan0 NS2_Net1_veth0  


sudo ip netns exec NS3 brctl addbr BR_vxlan0
sudo ip netns exec NS3 ip link set vxlan0 up
sudo ip netns exec NS3 ip link set BR_vxlan0 up
sudo ip netns exec NS3 brctl addif BR_vxlan0 vxlan0
sudo ip netns exec NS3 brctl addif BR_vxlan0 NS3_Net1_veth0  


