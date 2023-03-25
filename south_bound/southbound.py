import os
import json
import shutil
import ipaddress

import subprocess






# get the current working directory
cwd = os.getcwd()

# Navigate to the parent directory of south_bound
parent_dir = os.path.dirname(cwd)

# Navigate to the Network directory
network_json_file_path  = os.path.join(parent_dir, "north_bound", "Network","network.json")

# Open the file for reading
with open(network_json_file_path, 'r') as f:
    network_data = json.load(f)

vm_list = []
network_list = []


for tenant in  network_data:
    
    #print("Tenant name: ", network_data[tenant]["tenant_name"])
    #print("Tenant code: ", network_data[tenant]["tenant_code"])
    for vm in network_data[tenant]["VMs"]:
        vm_obj=vm
        vm_obj["tenant_name"] = network_data[tenant]["tenant_name"]
        vm_obj["tenant_code"] = network_data[tenant]["tenant_code"]
        vm_obj["connections"] = vm["connections"][0]["Connected_to"]
        vm_list.append(vm)
        #print("VM name: ", vm["vm_name"])
        #print("vCPUs: ", vm["vm_vcpus"])
        #print("RAM (MB): ", vm["vm_ram_mb"])
        #print("Disk size: ", vm["vm_disk_size"])
        #print("Connections: ", vm["connections"][0]["Connected_to"])
        #print("Status: ", vm["status"])
    
    for network in network_data[tenant]["Networks"]:
        network_obj=network
        network_obj["tenant_name"] = network_data[tenant]["tenant_name"]
        network_obj["tenant_code"] = network_data[tenant]["tenant_code"]
        network_obj["connections"] = network["connections"][0]["Connected_to"]
        network_list.append(network)
        #print("Network name: ", network["network_name"])
        #print("Subnet: ", network["subnet"])
        #print("Mask: ", network["mask"])
        #print("Connections: ", network["connections"][0]["Connected_to"])
        #print("Status: ", network["status"])
    #print("")


#print(vm_list)
#print(network_list)


playbook_path = os.path.join(cwd, "ansible_scripts","test.yml")
print(playbook_path)
inventory_path = os.path.join(cwd, "ansible_scripts","inventory.ini")
print(inventory_path)
extra_vars = {"var1": "value1", "var2": "value2"}



command = ['ansible-playbook', '-i', inventory_path, playbook_path]

for key, value in extra_vars.items():
    command.append("-e")
    command.append(f"{key}={value}")

process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
stdout, stderr = process.communicate()
if process.returncode != 0:
    print(f"Ansible playbook failed with error: {stderr.decode('utf-8')}")
else:
    print(f"Ansible playbook succeeded with output: {stdout.decode('utf-8')}")


