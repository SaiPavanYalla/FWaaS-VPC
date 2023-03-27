import os
import json
import shutil
import ipaddress
import datetime

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

with open('tenant_management.json', 'r') as file:
    # Parse the JSON data
    tenant_management_data = json.load(file)




input_sample_json = "inputTopology.json"

# Open the file for reading
with open(input_sample_json, 'r') as f:
    tenant_data = json.load(f)

# Get the tenant name and code
tenant_name = tenant_data['tenant_name']
tenant_code = tenant_data['tenant_code']

flag_if_present = False
namespace ="" 

for key, value in tenant_management_data.items():
        
        if value["tenant_name"] == tenant_name:
            flag_if_present = True
            namespace = key
            


if flag_if_present == False:
    print("Please enter Tenant details which are part of the VPC")
    exit()

tenant_data["namespace_tenant"] = namespace

source_path = os.getcwd() + "/" + input_sample_json
destination_path = os.path.join(os.getcwd(),"tenantTopology",tenant_name,"inputTopology_" + str(datetime.datetime.now()) + ".json")

#print(destination_path)

if not os.path.exists(os.path.join(os.getcwd(), "tenantTopology")):
    os.makedirs(os.path.join(os.getcwd(), "tenantTopology"))

if not os.path.exists(os.path.join(os.getcwd(), "tenantTopology",tenant_name)):
    os.makedirs(os.path.join(os.getcwd(), "tenantTopology",tenant_name))

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


   


# Iterate through each VM and get its properties
for vm in vms:
    vm["status"] = "Ready"
    vm_list.append(vm['vm_name'])
    vm["connection_status"] ={}
    connections = vm['connections'][0]['Connected_to']
    for connection in connections:
        vm["connection_status"][connection] = "Ready" 


#checking if VMs and Networks are duplicated or not in the sample.json file

vm_duplicates = []
network_duplicates = []

for vm in vm_list:
    if vm_list.count(vm) > 1 and vm not in vm_duplicates:
        vm_duplicates.append(vm)

for network in network_list:
    if network_list.count(network) > 1 and network not in network_duplicates:
        network_duplicates.append(network)



if vm_duplicates:
    print("These Guest VMs are duplicated in the Requirement File: ", vm_duplicates)
    exit()

if network_duplicates:
    print("These Networks are duplicated in the Requirement File: ", network_duplicates)
    exit()



    



tenant_data['VMs'] = vms
tenant_data['Networks'] = networks


#Now comes the appending part


network_destination_path = os.path.join(os.getcwd(), "Network")

existing_network_data ={}

if not os.path.exists(network_destination_path):
    os.makedirs(network_destination_path)

if os.path.exists(os.path.join(os.getcwd(), "Network","network.json")):
    with open(os.path.join(os.getcwd(), "Network","network.json") , 'r') as file:
        existing_network_data = json.load(file)


existing_vm_list=[]
existing_network_list = []







if existing_network_data:
    if tenant_name in existing_network_data.keys():

        #checking if the network or VM already exists in the Network.json
        for network in existing_network_data[tenant_name]["Networks"]:
            existing_network_list.append(network["network_name"])
            if network["network_name"] in network_list:
                print("The Network "+ network["network_name"] + "already exists in the Topology ")
                exit()

        for vm in existing_network_data[tenant_name]["VMs"]:
            existing_vm_list.append(vm["vm_name"])
            if vm["vm_name"] in vm_list:
                print("The VM "+ vm["vm_name"] + "already exists in the Topology ")
                exit()
        
        

        for vm in vms:
            connections = vm['connections'][0]['Connected_to']
            all_network_list = network_list + existing_network_list
            for connection in connections:
                if connection not in all_network_list:
                    print(connection + " is not a valid Network in yout Tenant")
                    exit()

        for network in tenant_data["Networks"]:
            existing_network_data[tenant_name]["Networks"].append(network)
        
        for vm in tenant_data["VMs"]:
            existing_network_data[tenant_name]["VMs"].append(vm)


    else:
        existing_network_data[tenant_name]= tenant_data
else:
    existing_network_data[tenant_name]= tenant_data

    
with open(network_destination_path + "/" + "network.json", "w") as f1:
    json.dump(existing_network_data, f1,indent=4)






