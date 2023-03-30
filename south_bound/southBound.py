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


def create_network(network,network_data,tenant,i):
    inventory_path = os.path.join(cwd, "inventory.ini")
    playbook_path = os.path.join(cwd, "ansible_scripts","create_ovs_bridge.yml")
    if network["status"] == "Ready": 
        mask = network["mask"]
        binary_octets = [bin(int(octet))[2:].zfill(8) for octet in mask.split(".")]
        cidr_prefix = sum([bin_octet.count("1") for bin_octet in binary_octets])
        cidr_notation = f"/{cidr_prefix}"
        ovs_network_address = ipaddress.IPv4Network((network['subnet'], mask))
        namespace_tenant = network_data[tenant]["namespace_tenant"]
        vm_net_name = network["network_name"]
        dhcp_start = ovs_network_address.network_address + 2
        dhcp_end = ovs_network_address.broadcast_address - 1
        tenant_net_gw_ip = str(ovs_network_address.network_address + 1) + str(cidr_notation)
        extra_vars = {'namespace_tenant': namespace_tenant  , 'vm_net_name': vm_net_name ,'dhcp_start': dhcp_start ,'dhcp_end': dhcp_end ,'tenant_net_gw_ip': tenant_net_gw_ip }
        command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
        sudo_password = "mmrj2023"

        for key, value in extra_vars.items():
            command.extend(['-e', f'{key}={value}'])

        
        network_data[tenant]["Networks"][i]["status"] = "Running"
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = process.communicate(sudo_password.encode())

        if process.returncode != 0:
            output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
            network_data[tenant]["Networks"][i]["status"] = "Ready"
            print(f"Ansible playbook failed with error while creating network:\n{output}")
        else:
            
            network_data[tenant]["Networks"][i]["status"] = "Completed"
    return network_data


def create_vm(vm,network_data,tenant,j):
    inventory_path = os.path.join(cwd, "inventory.ini")
    playbook_path = os.path.join(cwd, "ansible_scripts","create_vm.yml")
    hostname =  vm["vm_name"]
    namespace_tenant =  network_data[tenant]["namespace_tenant"]
    vm_vcpus = vm["vm_vcpus"]
    src_dir = os.path.join(cwd , "templates")
    vm_ram_mb =  vm["vm_ram_mb"]
    vm_disksize_gb = int(vm["vm_disk_size"])

    extra_vars = {'hostname': hostname,'namespace_tenant' : namespace_tenant , 'vm_vcpus': vm_vcpus ,'src_dir': src_dir ,'vm_ram_mb': vm_ram_mb ,'vm_disksize_gb': vm_disksize_gb }

    command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
    sudo_password = "mmrj2023"

    for key, value in extra_vars.items():
        if key == "vm_disksize_gb" or key == "vm_vcpus" or key == "vm_ram_mb" :
            value = int(value)
        command.extend(['-e', f'{key}={value}'])

    
    network_data[tenant]["VMs"][j]["status"] = "Running"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    stdout, stderr = process.communicate(sudo_password.encode())

    if process.returncode != 0:
        output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
        network_data[tenant]["VMs"][j]["status"] = "Ready"
        print(f"Ansible playbook failed with error while creating a VM :\n{output}")
    else:
        network_data[tenant]["VMs"][j]["status"] = "Completed"
    return network_data


def attach_interface(vm,network_data,tenant,connection,k):
    inventory_path = os.path.join(cwd, "inventory.ini")
    playbook_path = os.path.join(cwd, "ansible_scripts","attach_ovs_bridge.yml")

    namespace_tenant = network_data[tenant]["namespace_tenant"]
    hostname = vm["vm_name"]
    vm_net_name = connection
    src_dir= os.path.join(cwd , "templates")
    extra_vars = {'hostname': hostname  , 'namespace_tenant': namespace_tenant ,'src_dir': src_dir ,'vm_net_name': vm_net_name }

    command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
    sudo_password = "mmrj2023"

    for key, value in extra_vars.items():
        command.extend(['-e', f'{key}={value}'])


    network_data[tenant]["VMs"][k]["connection_status"][connection] = "Running"
    

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    stdout, stderr = process.communicate(sudo_password.encode())

    if process.returncode != 0:
        output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
        network_data[tenant]["VMs"][k]["connection_status"][connection] = "Ready"
        
        print(f"Ansible playbook failed with error while creating a VM :\n{output}")
    else:
        
        network_data[tenant]["VMs"][k]["connection_status"][connection] = "Completed"







for tenant in  network_data:
    #create networks
    i=0
    for network in network_data[tenant]["Networks"]:
        
        network_data = create_network(network,network_data,tenant,i)
        i=i+1
            


    #create VMs
    j=0 
    for vm in network_data[tenant]["VMs"]:
        if vm["status"] == "Ready":
            network_data = create_vm(vm,network_data,tenant,j)
        j=j+1

    #attach interface
    k=0
    for vm in network_data[tenant]["VMs"]:
        if vm["status"] == "Completed":
            for connection in vm["connections"][0]["Connected_to"]:
                if vm["connection_status"][connection] == "Ready": 
                    for network in network_data[tenant]["Networks"]:
                        if connection == network["network_name"]:
                            if network["status"] == "Completed":
                                attach_interface(vm,network_data,tenant,connection,k)
        k=k+1
    
    #Creation of Firewall
    if  "Firewall" in network_data[tenant].keys():
        firewall_data = network_data[tenant]["Firewall"]
        #Create int fw net
        if  firewall_data["status"]["internal_net_status"] == "Ready":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","create_ovs_bridge.yml")
            mask = "255.255.255.0"
            binary_octets = [bin(int(octet))[2:].zfill(8) for octet in mask.split(".")]
            cidr_prefix = sum([bin_octet.count("1") for bin_octet in binary_octets])
            cidr_notation = f"/{cidr_prefix}"
            ovs_network_address = ipaddress.IPv4Network((firewall_data["firewall_internal_subnet"], mask))
            namespace_tenant = network_data[tenant]["namespace_tenant"]
            vm_net_name = "FwI" 
            dhcp_start = ovs_network_address.network_address + 2
            dhcp_end = ovs_network_address.broadcast_address - 1
            tenant_net_gw_ip = str(ovs_network_address.network_address + 1) + str(cidr_notation)
            extra_vars = {'namespace_tenant': namespace_tenant  , 'vm_net_name': vm_net_name ,'dhcp_start': dhcp_start ,'dhcp_end': dhcp_end ,'tenant_net_gw_ip': tenant_net_gw_ip }
            command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
            sudo_password = "mmrj2023"

            for key, value in extra_vars.items():
                command.extend(['-e', f'{key}={value}'])

            
            firewall_data["status"]["internal_net_status"] = "Running"
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = process.communicate(sudo_password.encode())

            if process.returncode != 0:
                output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                firewall_data["status"]["internal_net_status"] = "Ready"
                print(f"Ansible playbook failed with error while creating Internal network of Firewall:\n{output}")
            else:
                
                firewall_data["status"]["internal_net_status"] = "Completed"
        
        #Create ext fw net
        if  firewall_data["status"]["external_net_status"] == "Ready":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","create_ovs_bridge.yml")
            mask = "255.255.255.0"
            binary_octets = [bin(int(octet))[2:].zfill(8) for octet in mask.split(".")]
            cidr_prefix = sum([bin_octet.count("1") for bin_octet in binary_octets])
            cidr_notation = f"/{cidr_prefix}"
            ovs_network_address = ipaddress.IPv4Network((firewall_data["firewall_external_subnet"], mask))
            namespace_tenant = network_data[tenant]["namespace_tenant"]
            vm_net_name = "FwE" 
            dhcp_start = ovs_network_address.network_address + 2
            dhcp_end = ovs_network_address.broadcast_address - 1
            tenant_net_gw_ip = str(ovs_network_address.network_address + 1) + str(cidr_notation)
            extra_vars = {'namespace_tenant': namespace_tenant  , 'vm_net_name': vm_net_name ,'dhcp_start': dhcp_start ,'dhcp_end': dhcp_end ,'tenant_net_gw_ip': tenant_net_gw_ip }
            command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
            sudo_password = "mmrj2023"

            for key, value in extra_vars.items():
                command.extend(['-e', f'{key}={value}'])

            
            firewall_data["status"]["external_net_status"] = "Running"
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = process.communicate(sudo_password.encode())

            if process.returncode != 0:
                output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                firewall_data["status"]["external_net_status"] = "Ready"
                print(f"Ansible playbook failed with error while creating External network of Firewall:\n{output}")
            else:
                
                firewall_data["status"]["external_net_status"] = "Completed"
        
        #Firewall VM creation
        if  firewall_data["status"]["firewall_status"] == "Ready":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","create_vm.yml")
            
            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            hostname =  "FW"
            vm_vcpus = firewall_data["firewall_vcpus"]
            src_dir = os.path.join(cwd , "templates")
            vm_ram_mb =  firewall_data["firewall_ram_mb"]
            vm_disksize_gb = firewall_data["firewall_disk_size"]

            extra_vars = {'hostname': hostname,'namespace_tenant' : namespace_tenant , 'vm_vcpus': vm_vcpus ,'src_dir': src_dir ,'vm_ram_mb': vm_ram_mb ,'vm_disksize_gb': vm_disksize_gb }

            command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
            sudo_password = "mmrj2023"

            for key, value in extra_vars.items():
                if key == "vm_disksize_gb" or key == "vm_vcpus" or key == "vm_ram_mb" :
                    value = int(value)
                command.extend(['-e', f'{key}={value}'])

            
            firewall_data["status"]["firewall_status"] = "Running"
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = process.communicate(sudo_password.encode())

            if process.returncode != 0:
                output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                firewall_data["status"]["firewall_status"] = "Ready"
                print(f"Ansible playbook failed with error while creating a VM :\n{output}")
            else:
                firewall_data["status"]["firewall_status"] = "Completed"

        #Attach int fw net
        if  firewall_data["status"]["internal_net_attach_status"] == "Ready" and firewall_data["status"]["firewall_status"] == "Completed" and firewall_data["status"]["internal_net_status"] == "Completed":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","attach_ovs_bridge.yml")

            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            hostname =  "FW"
            vm_net_name = "FwI"
            src_dir= os.path.join(cwd , "templates")
            extra_vars = {'hostname': hostname  , 'namespace_tenant': namespace_tenant ,'src_dir': src_dir ,'vm_net_name': vm_net_name }

            command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
            sudo_password = "mmrj2023"

            for key, value in extra_vars.items():
                command.extend(['-e', f'{key}={value}'])


            firewall_data["status"]["internal_net_attach_status"] = "Running"
            

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = process.communicate(sudo_password.encode())

            if process.returncode != 0:
                output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                firewall_data["status"]["internal_net_attach_status"] = "Ready"
                
                print(f"Ansible playbook failed with error while creating a VM :\n{output}")
            else:
                firewall_data["status"]["internal_net_attach_status"] = "Completed"



        #Attach ext fw net
        if  firewall_data["status"]["external_net_attach_status"] == "Ready" and firewall_data["status"]["firewall_status"] == "Completed" and firewall_data["status"]["external_net_status"] == "Completed":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","attach_ovs_bridge.yml")

            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            hostname =  "FW"
            vm_net_name = "FwE"
            src_dir= os.path.join(cwd , "templates")
            extra_vars = {'hostname': hostname  , 'namespace_tenant': namespace_tenant ,'src_dir': src_dir ,'vm_net_name': vm_net_name }

            command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
            sudo_password = "mmrj2023"

            for key, value in extra_vars.items():
                command.extend(['-e', f'{key}={value}'])


            firewall_data["status"]["external_net_attach_status"] = "Running"
            

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = process.communicate(sudo_password.encode())

            if process.returncode != 0:
                output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                firewall_data["status"]["external_net_attach_status"] = "Ready"
                
                print(f"Ansible playbook failed with error while creating a VM :\n{output}")
            else:
                firewall_data["status"]["external_net_attach_status"] = "Completed"






with open(network_json_file_path, "w") as outfile:
    # write the JSON data to the file
    json.dump(network_data, outfile,indent=4)       
