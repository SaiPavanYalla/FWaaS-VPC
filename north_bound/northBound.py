import os
import json
import shutil
import ipaddress


def validate_subnet_mask(subnet_mask):
    try:
        ipaddress.IPv4Network('0.0.0.0/' + subnet_mask)
        return True
    except ValueError:
        return False

def validate_network_address(network_address, subnet_mask):
    try:
        network = ipaddress.IPv4Network(network_address + '/' + subnet_mask)
        return str(network.network_address) == network_address
    except ValueError:
        return False

input_sample_json = "sample.json"

# Open the file for reading
with open(input_sample_json, 'r') as f:
    tenant_data = json.load(f)

# Get the tenant name and code
tenant_name = tenant_data['tenant_name']
tenant_code = tenant_data['tenant_code']


source_path = os.getcwd() + "/" + input_sample_json
destination_path = os.getcwd() + "/" + tenant_name

if not os.path.exists(destination_path):
    os.makedirs(destination_path)

shutil.copy(source_path,destination_path )


# Get the list of VMs
vms = tenant_data['VMs']

# Get the list of networks
networks = tenant_data['Networks']

vm_list =[]
network_list =[]

# Iterate through each network and get its properties
for network in networks:
    network["status"] = "Ready"
    network_list.append(network['network_name'])

    if not validate_subnet_mask(network['mask']):
        print("invalid subnet mask for "+ network["network_name"])
        exit()

    if not validate_network_address(network['subnet'],network['mask']):
        print("invalid network address for "+ network["network_name"])
        exit()


    #network_name = network['network_name']
    #subnet = network['subnet']
    #mask = network['mask']
    #connections = network['connections'][0]['Connected_to']


# Iterate through each VM and get its properties
for vm in vms:
    vm["status"] = "Ready"
    vm_list.append(vm['vm_name'])
    #vm_name = vm['vm_name']
    #vm_vcpus = vm['vm_vcpus']
    #vm_ram_mb = vm['vm_ram_mb']
    #vm_disk_size = vm['vm_disk_size']
    #connections = vm['connections'][0]['Connected_to']

    
for network in networks:
    connections = network['connections'][0]['Connected_to']
    for connection in connections:
        if connection not in vm_list:
            print(connection + " is not a valid device ")
            exit()

for vm in vms:
    connections = vm['connections'][0]['Connected_to']
    for connection in connections:
        if connection not in network_list:
            print(connection + " is not a valid Network")
            exit()


tenant_data['VMs'] = vms
tenant_data['Networks'] = networks
  
network_destination_path = os.getcwd() + "/" + "Network"

if not os.path.exists(network_destination_path):
    os.makedirs(network_destination_path)


if os.path.exists(network_destination_path + "/" + "network.json"):
    with open(network_destination_path + "/" + "network.json", "r") as f:   
        existing_data = json.load(f)
        existing_data[tenant_name]= tenant_data
    
        with open(network_destination_path + "/" + "network.json", "w") as f1:
            json.dump(existing_data, f1)

else:
    with open(network_destination_path + "/" + "network.json", "w") as f:
        tenant_json_data ={}
        tenant_json_data[tenant_name] = tenant_data
        json.dump(tenant_json_data, f)




