import csv
import ipaddress

def is_valid_ipv4_address(address):
    try:
        # Try to create an IPv4Address object
        ipaddress.IPv4Address(address)
        return True
    except ipaddress.AddressValueError:
        # The address is not a valid IPv4 address
        return False

def is_valid_port(port):
    try:
        port = int(port)
        if port >= 1 and port <= 65535:
            return True
        if str(port) == "any":
            return True
        else:
            return False
    except ValueError:
        return False

def are_dicts_equal_except_key(d1, d2, key1,key2):
    d1_copy = d1.copy()
    d2_copy = d2.copy()
    d1_copy.pop(key1, None)
    d1_copy.pop(key2, None)
    d2_copy.pop(key1, None)
    d2_copy.pop(key2, None)
    return d1_copy == d2_copy

firewall_policy_list = []

tenant_name = input("Please enter your Tenant Name")
tenant_code = input("Please enter your Tenant Code")


network_data = {}
if os.path.exists(os.path.join(os.getcwd(), "Network","network.json")):
    with open(os.path.join(os.getcwd(), "Network","network.json") , 'r') as file:
        network_data = json.load(file)

if not tenant_name in network_data.keys():
    print("Tenant Network is not created. Please create Tenant Network")
    exit()
else:
    if not tenant_code == network_data[tenant_name]["tenant_code"] 
        print("Please type the correct Tenant Code")
        exit()
    if not ( "Firewall" in network_data[tenant_name].keys() and all(val == "Completed" for val in network_data[tenant_name]["Firewall"]["status"].values())) :
        print("Please create a Firewall and apply policies to the Tenant Network")
        exit()


def execute_firewall_policy(firewall_policy_obj):
    
    parent_dir = os.path.dirname(cwd)

    inventory_path = os.path.join(parent_dir,"south_bound", "firewall.ini")
    playbook_path = os.path.join(parent_dir,"south_bound", "ansible_scripts","add_fw_rule.yml")

    src_ip = firewall_policy_obj["src_ip"]
    dest_ip = firewall_policy_obj["dest_ip"]
    src_port= firewall_policy_obj["src_port"]
    dest_port = firewall_policy_obj["dest_port"]
    protocol = firewall_policy_obj["protocol"]
    threshold = firewall_policy_obj["threshold"]
    host = network_data[tenant]["namespace_tenant"] + "FW"        

    
    extra_vars = { 'src_ip': src_ip ,'dest_ip': dest_ip , 'src_port': src_port ,'dest_port': dest_port, 'protocol': protocol , 'threshold': threshold , 'host': host }

    command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
    sudo_password = "mmrj2023"

    for key, value in extra_vars.items():
        command.extend(['-e', f'{key}={value}'])


    
    #This is to add to network json
    policy_obj = extra_vars
    policy_obj["Status"] = "Ready"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    stdout, stderr = process.communicate(sudo_password.encode())

    if not "Policies" in firewall_data.keys():
        firewall_data["Policies"]= {}

    flag = True
    for policy in firewall_data["Policies"]:
        if are_dicts_equal_except_key(policy,policy_obj,"Status"):
            flag = False

    if process.returncode != 0:
        output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
        policy_obj["Status"] = "Failed"
        
        if flag = True:        
            firewall_data["Policies"].append(policy_obj)
        print(f"Ansible playbook failed with error while adding a Policy :\n{output}")
        print(policy_obj)
    else:
        policy_obj["Status"] = "Completed"
        if flag = True:        
            firewall_data["Policies"].append(policy_obj)
        






#Deleting firewall policies which are not in the requirement file

if "Policies" in network_data[tenant_name]["Firewall"].keys():
    existing_firewall_policies = network_data[tenant_name]["Firewall"]["keys"]


with open('firewallPolicies.csv', 'r') as file:
    reader = csv.DictReader(file)
    for firewall_policy_obj in reader:
        firewall_policy_list.append(row)
        if not (is_valid_ipv4_address(firewall_policy_obj["src_ip"]) and is_valid_ipv4_address(firewall_policy_obj["dest_ip"])):
            print("The IP addresses given are not valid in the row below")
            print(firewall_policy_obj)

        if not (is_valid_port(firewall_policy_obj["src_port"]) and is_valid_port(firewall_policy_obj["dest_port"]) ):
            print("The Port Numbers given are not valid in the row below")
            print(firewall_policy_obj)

        execute_firewall_policy(firewall_policy_obj)


with open(os.path.join(os.getcwd(), "Network","network.json"), "w") as f1:
    json.dump(network_data, f1,indent=4)








