import os
import json
import shutil
import ipaddress
import ansible_runner
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

inventory_path = os.path.join(cwd, "inventory.ini")


#First step is to create networks
for tenant in  network_data:
    playbook_path = os.path.join(cwd, "ansible_scripts","create_net_lib_route.yml")
    i=0
    for network in network_data[tenant]["Networks"]:
        i=i+1
            if network["status"] == "Pending":

                net= network['network_name']
                mask=  network['mask']
                network = ipaddress.IPv4Network((network['subnet'], mask))
                start = network.network_address + 2
                end = network.broadcast_address - 1
                gw= network.network_address + 1
            
                extra_vars = {'net': net  , 'mask': mask ,'gw': gw ,'start': start ,'end': end }

                command = ['ansible-playbook', playbook_path ,'-i', inventory_path]

                for key, value in extra_vars.items():
                    command.extend(['-e', f'{key}={value}'])

                

                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()

                if process.returncode != 0:
                    output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                    network_data[tenant]["Networks"][i]["status"] = "Pending"
                    #print(f"Ansible playbook failed with error:\n{output}")
                else:
                    #print(f"Ansible playbook succeeded with output:\n{stdout.decode('utf-8')}")
                    network_data[tenant]["Networks"][i]["status"] = "Completed"
                
                #print("Status: ", network['status'])
                #print("Tenant Name: ", network['tenant_name'])
                #print("Tenant Code: ", network['tenant_code'])
            
     

with open(network_json_file_path, "w") as outfile:
    # write the JSON data to the file
    json.dump(network_data, outfile)       
