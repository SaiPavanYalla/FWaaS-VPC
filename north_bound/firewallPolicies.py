import csv
import ipaddress
import os 
import json
import subprocess


def is_valid_ipv4_address(address):
    try:
        ip_network = ipaddress.IPv4Network(address)
        return (ip_network.is_private and not ip_network.is_multicast)
    except ipaddress.AddressValueError:
        # The address is not a valid IPv4 address
        return False

def is_valid_port(port):
    try:
        if str(port) == "any":
            return True
        
        port = int(port)
        if port >= 1 and port <= 65535:
            return True
        else:
            return False
    except ValueError:
        return False

def are_dicts_equal_except_key(d1, d2, key):
    d1_copy = d1.copy()
    d2_copy = d2.copy()
    d1_copy.pop(key, None)
    
    d2_copy.pop(key, None)
   
    return d1_copy == d2_copy

firewall_policy_list = []

tenant_name =  "team36"
tenant_code = "123456"

#tenant_name = input("Please enter your Tenant Name: ") 
#tenant_code = input("Please enter your Tenant Code: ") 


network_data = {}
if os.path.exists(os.path.join(os.getcwd(), "Infrastructure","infrastructure.json")):
    with open(os.path.join(os.getcwd(), "Infrastructure","infrastructure.json") , 'r') as file:
        network_data = json.load(file)

if not tenant_name in network_data.keys():
    print("Tenant Network is not created. Please create Tenant Network")
    exit()
else:
    if not tenant_code == network_data[tenant_name]["tenant_code"] :
        print("Please type the correct Tenant Code")
        exit()
    if not ( "Firewall" in network_data[tenant_name].keys() and all(val == "Completed" for val in network_data[tenant_name]["Firewall"]["status"].values())) :
        print("Please create a Firewall and apply policies to the Tenant Network")
        exit()


def execute_firewall_policy(add_firewall_policy):
    
    parent_dir = os.path.dirname(os.getcwd())

    inventory_path = os.path.join(parent_dir,"south_bound", "inventory.ini")
    playbook_path = os.path.join(parent_dir,"south_bound", "ansible_scripts","add_fw_rule.yml")
    add_firewall_policy["host"] = network_data[tenant_name]["namespace_tenant"] + "FW"        
    command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path,"--ask-become-pass"]
    sudo_password = "mmrj2023"
    
    for key, value in add_firewall_policy.items():
        command.extend(['-e', f'{key}={value}'])

    add_firewall_policy.pop("host",None)

    status = "Ready"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    stdout, stderr = process.communicate(sudo_password.encode())
    if process.returncode != 0:
        output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
        status = "Ready"
        print(f"Ansible playbook failed with error while adding a Policy :\n{output}")
        print(add_firewall_policy)
    else:
        status = "Completed"
        

    return status


def delete_firewall_policy(del_firewall_policy):
    
    parent_dir = os.path.dirname(os.getcwd())

    inventory_path = os.path.join(parent_dir,"south_bound", "inventory.ini")
    playbook_path = os.path.join(parent_dir,"south_bound", "ansible_scripts","del_fw_rule.yml")
    del_firewall_policy["host"] = network_data[tenant_name]["namespace_tenant"] + "FW"        
    command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path,"--ask-become-pass"]
    sudo_password = "mmrj2023"

    for key, value in del_firewall_policy.items():
        command.extend(['-e', f'{key}={value}'])
    
    del_firewall_policy.pop("host",None)

    status = "Deleted"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    stdout, stderr = process.communicate(sudo_password.encode())
    if process.returncode != 0:
        output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
        status = "Delete"
        print(f"Ansible playbook failed with error while deleting a Policy :\n{output}")
        print(del_firewall_policy)
    else:
        status = "Deleted"
        

    return status







#making firewall policy list and taking all that into a dictionary
firewall_policy_list = []

with open('firewallPolicies.csv', 'r') as file:
    reader = csv.DictReader(file)
    for firewall_policy_obj in reader:
        if not (is_valid_ipv4_address(firewall_policy_obj["src_ip"]) and is_valid_ipv4_address(firewall_policy_obj["dest_ip"])):
            print("The IP addresses given are not valid in the row below")
            print(firewall_policy_obj)
            exit()

        if not (is_valid_port(firewall_policy_obj["src_port"]) and is_valid_port(firewall_policy_obj["dest_port"]) ):
            print("The Port Numbers given are not valid in the row below")
            print(firewall_policy_obj)
            exit()
        else:
            if firewall_policy_obj["src_port"] == "any":
                firewall_policy_obj["src_port"] = "0-65535"

            if firewall_policy_obj["dest_port"] == "any":
                firewall_policy_obj["dest_port"] = "0-65535"


        if not (firewall_policy_obj["policy_action"] == "ACCEPT" or firewall_policy_obj["policy_action"] == "DROP" ):
            print("The Policy action is not valid it should be ACCEPT or DROP")
            print(firewall_policy_obj)
            exit()
    
        firewall_policy_list.append(firewall_policy_obj)


existing_firewall_policies = []

if "Policies" in network_data[tenant_name]["Firewall"].keys():
    existing_firewall_policies =  network_data[tenant_name]["Firewall"]["Policies"]


#Delete all the ones which has Delete status
for existing_firewall_policy in existing_firewall_policies:

    if existing_firewall_policy["status"] == "Delete":
        status = delete_firewall_policy(existing_firewall_policy)
        if status == "Deleted":
            existing_firewall_policies.remove(existing_firewall_policy)
        

network_data[tenant_name]["Firewall"]["Policies"] = existing_firewall_policies



#Deleting firewall policies which are not in the requirement file


    
i=0
for existing_firewall_policy in existing_firewall_policies:
    flag_NA = True
    
    for firewall_policy in firewall_policy_list:
        if are_dicts_equal_except_key(firewall_policy,existing_firewall_policy,"status"):
            flag_NA = False
    
    if flag_NA:
        
        if existing_firewall_policy["status"] == "Completed":
            status = delete_firewall_policy(existing_firewall_policy)
            if status == "Deleted":
                existing_firewall_policies.remove(existing_firewall_policy)
            else:
                existing_firewall_policies[i]["status"] = "Delete"

        if existing_firewall_policy["status"] == "Ready":
            existing_firewall_policies.remove(existing_firewall_policy)
    i+=1
            

network_data[tenant_name]["Firewall"]["Policies"] = existing_firewall_policies

#Executing existing firewall policies which are in the requirement file and not completed


for firewall_policy in firewall_policy_list:
    i=0
    status = "Ready"
    for existing_firewall_policy in existing_firewall_policies:
        
        if are_dicts_equal_except_key(firewall_policy,existing_firewall_policy,"status"):
            if existing_firewall_policy["status"] == "Ready":
                status = execute_firewall_policy(firewall_policy)
                existing_firewall_policies[i]["status"] = status
        i+=1
    
    flag_NA = True
    
    for existing_firewall_policy in existing_firewall_policies:
        if are_dicts_equal_except_key(firewall_policy,existing_firewall_policy,"status"):
            flag_NA = False
    if flag_NA:
        # print("in here")
        # print(flag_NA)
        # print(existing_firewall_policies)
        # print(firewall_policy)
        status = execute_firewall_policy(firewall_policy)
        firewall_policy["status"] = status 
        existing_firewall_policies.append(firewall_policy)
        

            

network_data[tenant_name]["Firewall"]["Policies"] = existing_firewall_policies  

#executing the one's which are not in the 



with open(os.path.join(os.getcwd(), "Infrastructure","infrastructure.json"), "w") as f1:
    json.dump(network_data, f1,indent=4)








