import os
import json
import ipaddress
import subprocess

# get the current working directory
cwd = os.getcwd()

# Navigate to the parent directory of south_bound
parent_dir = os.path.dirname(cwd)

# Navigate to the Network directory
network_json_file_path  = os.path.join(parent_dir, "north_bound", "Infrastructure","infrastructure.json")

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
            print(f" The Network {vm_net_name} has been successfully created in {namespace_tenant}.")
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
        print(f" The Guest VM {hostname} has been successfully created in {namespace_tenant}.")
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
        print(f" The Interface/Connection has been successfully created between {hostname} and {vm_net_name} in {namespace_tenant}.")







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
    

    if  "Firewall" in network_data[tenant].keys():
        firewall_data = network_data[tenant]["Firewall"]
         #Create int fw net
        if  firewall_data["status"]["internal_net_status"] == "Ready":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","create_fw_ovs_bridge.yml")
            mask = "255.255.255.0"
            binary_octets = [bin(int(octet))[2:].zfill(8) for octet in mask.split(".")]
            cidr_prefix = sum([bin_octet.count("1") for bin_octet in binary_octets])
            cidr_notation = f"/{cidr_prefix}"
            ovs_network_address = ipaddress.IPv4Network(("10.7.7.0", mask))
            namespace_tenant = network_data[tenant]["namespace_tenant"]
            vm_net_name = "FwI" 
            dhcp_start = ovs_network_address.network_address + 2
            dhcp_end = ovs_network_address.network_address + 3
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
                print(f"Ansible playbook failed with error while creating Internal network of Master Firewall:\n{output}")
            else:
                print(f" The Internal network {vm_net_name} for Master Firewall has been successfully created in {namespace_tenant}.")
                firewall_data["status"]["internal_net_status"] = "Completed"
        
        #Create ext fw net
        if  firewall_data["status"]["external_net_status"] == "Ready":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","create_fw_ovs_bridge.yml")
            mask = "255.255.255.0"
            binary_octets = [bin(int(octet))[2:].zfill(8) for octet in mask.split(".")]
            cidr_prefix = sum([bin_octet.count("1") for bin_octet in binary_octets])
            cidr_notation = f"/{cidr_prefix}"
            ovs_network_address = ipaddress.IPv4Network(("10.8.8.0", mask))
            namespace_tenant = network_data[tenant]["namespace_tenant"]
            vm_net_name = "FwE" 
            dhcp_start = ovs_network_address.network_address + 2
            dhcp_end = ovs_network_address.network_address + 3
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
                print(f"Ansible playbook failed with error while creating External network of Master Firewall:\n{output}")
            else:
                
                firewall_data["status"]["external_net_status"] = "Completed"
                print(f" The External network {vm_net_name} for Master Firewall  has been successfully created in {namespace_tenant}.")



    #Creation of Firewall MASTER
    if  "Firewall" in network_data[tenant].keys():
        firewall_data = network_data[tenant]["Firewall"]["Firewall_master"]

        #Firewall VM creation
        if  firewall_data["status"]["firewall_status"] == "Ready":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","create_vm.yml")
            
            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            hostname =  "FW1"
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
                print(f"Ansible playbook failed with error while creating a Master firewall VM :\n{output}")
            else:
                firewall_data["status"]["firewall_status"] = "Completed"
                print(f" The Master Firewall {hostname} has been successfully created in {namespace_tenant}.")

        #attach management to firewall
        if  firewall_data["status"]["mgmt_net_attach_status"] == "Ready" and firewall_data["status"]["firewall_status"] == "Completed" :
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","attach_mgmt.yml")
           
            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            last_mac ='{:02X}'.format(int(namespace_tenant.replace("T","")))
            vm_name = namespace_tenant + "FW1" 
            src_dir= os.path.join(cwd , "templates")
            extra_vars = { 'namespace_tenant': namespace_tenant ,'vm_name': vm_name, 'last_mac': last_mac ,'src_dir': src_dir }

            command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
            sudo_password = "mmrj2023"

            for key, value in extra_vars.items():
                command.extend(['-e', f'{key}={value}'])


            firewall_data["status"]["mgmt_net_attach_status"] = "Running"
            

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = process.communicate(sudo_password.encode())

            if process.returncode != 0:
                output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                firewall_data["status"]["mgmt_net_attach_status"] = "Ready"
                
                print(f"Ansible playbook failed with error while creating a management network attach for Master firewall :\n{output}")
            else:
                firewall_data["status"]["mgmt_net_attach_status"] = "Completed"
                print(f" The Management Interface/Connection has been successfully created between Master firewall  and Host VM in {namespace_tenant}.")




        firewall_data_overview =  network_data[tenant]["Firewall"]

        #Attach int fw net
        if  firewall_data["status"]["internal_net_attach_status"] == "Ready" and firewall_data["status"]["firewall_status"] == "Completed" and firewall_data_overview["status"]["internal_net_status"] == "Completed":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","attach_ovs_bridge.yml")

            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            hostname =  "FW1"
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
                
                print(f"Ansible playbook failed with error while creating a internal network attach for Master firewall :\n{output}")
            else:
                firewall_data["status"]["internal_net_attach_status"] = "Completed"
                print(f" The Internal Interface/Connection has been successfully created between Master firewall {hostname} and Internal Network {vm_net_name} in {namespace_tenant}.")


        firewall_data_overview = network_data[tenant]["Firewall"]
        #Attach ext fw net
        if  firewall_data["status"]["external_net_attach_status"] == "Ready" and firewall_data["status"]["firewall_status"] == "Completed" and firewall_data_overview["status"]["external_net_status"] == "Completed":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","attach_ovs_bridge.yml")

            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            hostname =  "FW1"
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
                
                print(f"Ansible playbook failed with error while creating a external network attach for Master Firewall :\n{output}")
            else:
                firewall_data["status"]["external_net_attach_status"] = "Completed"
                print(f" The External Interface/Connection has been successfully created between Master firewall {hostname} and External Network {vm_net_name} in {namespace_tenant}.")

       
        

        #create firewall control plane
        if firewall_data["status"]["firewall_status"] == "Completed" and firewall_data["status"]["internal_net_attach_status"] == "Completed" and  firewall_data["status"]["external_net_attach_status"] == "Completed" and firewall_data["status"]["fw_control_plane"] == "Ready":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","fw_control_plane.yml")
            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            hostname = "FW1"

            extra_vars = {'hostname': hostname ,'namespace_tenant' : namespace_tenant  }

            command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
            sudo_password = "mmrj2023"

            for key, value in extra_vars.items():
                command.extend(['-e', f'{key}={value}'])
            
            firewall_data["status"]["fw_control_plane"] = "Running"  
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = process.communicate(sudo_password.encode())

            if process.returncode != 0:
                output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                firewall_data["status"]["fw_control_plane"] = "Ready"                
                print(f"Ansible playbook failed with error while creating Master firewall control plane:\n{output}")
            else:
                firewall_data["status"]["fw_control_plane"] = "Completed"
                print(f" create Master firewall control plane successfully created in {namespace_tenant}.")



#Creation of Firewall Backup
    if  "Firewall" in network_data[tenant].keys():
        firewall_data = network_data[tenant]["Firewall"]["Firewall_backup"]

        
        #Firewall VM creation
        if  firewall_data["status"]["firewall_status"] == "Ready":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","create_vm.yml")
            
            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            hostname =  "FW2"
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
                print(f"Ansible playbook failed with error while creating a Backup firewall VM :\n{output}")
            else:
                firewall_data["status"]["firewall_status"] = "Completed"
                print(f" The Backup Firewall {hostname} has been successfully created in {namespace_tenant}.")

        #attach management to firewall
        if  firewall_data["status"]["mgmt_net_attach_status"] == "Ready" and firewall_data["status"]["firewall_status"] == "Completed" :
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","attach_mgmt.yml")
           
            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            last_mac ='{:02X}'.format(int(namespace_tenant.replace("T",""))+100)
            vm_name = namespace_tenant + "FW2" 
            src_dir= os.path.join(cwd , "templates")
            extra_vars = { 'namespace_tenant': namespace_tenant ,'vm_name': vm_name, 'last_mac': last_mac ,'src_dir': src_dir }

            command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
            sudo_password = "mmrj2023"

            for key, value in extra_vars.items():
                command.extend(['-e', f'{key}={value}'])


            firewall_data["status"]["mgmt_net_attach_status"] = "Running"
            

            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = process.communicate(sudo_password.encode())

            if process.returncode != 0:
                output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                firewall_data["status"]["mgmt_net_attach_status"] = "Ready"
                
                print(f"Ansible playbook failed with error while creating a management network attach for Backup Firewall :\n{output}")
            else:
                firewall_data["status"]["mgmt_net_attach_status"] = "Completed"
                print(f" The Management Interface/Connection has been successfully created between Backup firewall  and Host VM in {namespace_tenant}.")


        #Attach int fw net
        firewall_data_overview =  network_data[tenant]["Firewall"]
        if  firewall_data["status"]["internal_net_attach_status"] == "Ready" and firewall_data["status"]["firewall_status"] == "Completed" and firewall_data_overview["status"]["internal_net_status"] == "Completed" :
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","attach_ovs_bridge.yml")

            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            hostname =  "FW2"
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
                
                print(f"Ansible playbook failed with error while creating a internal network attach for Backup Firewall :\n{output}")
            else:
                firewall_data["status"]["internal_net_attach_status"] = "Completed"
                print(f" The Internal Interface/Connection has been successfully created between Backup firewall {hostname} and Internal Network {vm_net_name} in {namespace_tenant}.")


        firewall_data_overview =  network_data[tenant]["Firewall"]
        #Attach ext fw net
        if  firewall_data["status"]["external_net_attach_status"] == "Ready" and firewall_data["status"]["firewall_status"] == "Completed" and firewall_data_overview["status"]["external_net_status"] == "Completed":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","attach_ovs_bridge.yml")

            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            hostname =  "FW2"
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
                
                print(f"Ansible playbook failed with error while creating a external network attach for Backup Firewall :\n{output}")
            else:
                firewall_data["status"]["external_net_attach_status"] = "Completed"
                print(f" The External Interface/Connection has been successfully created between Backup firewall {hostname} and External Network {vm_net_name} in {namespace_tenant}.")

    #create firewall control plane
        if firewall_data["status"]["firewall_status"] == "Completed" and firewall_data["status"]["internal_net_attach_status"] == "Completed" and  firewall_data["status"]["external_net_attach_status"] == "Completed" and firewall_data["status"]["fw_control_plane"] == "Ready":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","fw_control_plane.yml")
            namespace_tenant =  network_data[tenant]["namespace_tenant"]
            hostname = "FW2"

            extra_vars = {'hostname': hostname ,'namespace_tenant' : namespace_tenant  }

            command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
            sudo_password = "mmrj2023"

            for key, value in extra_vars.items():
                command.extend(['-e', f'{key}={value}'])
            
            firewall_data["status"]["fw_control_plane"] = "Running"  
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = process.communicate(sudo_password.encode())

            if process.returncode != 0:
                output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                firewall_data["status"]["fw_control_plane"] = "Ready"                
                print(f"Ansible playbook failed with error while creating Backup firewall control plane:\n{output}")
            else:
                firewall_data["status"]["fw_control_plane"] = "Completed"
                print(f" create Backup firewall control plane successfully created in {namespace_tenant}.")

        

        
        #create table to re-route traffic
        firewall_data_master = network_data[tenant]["Firewall"]["Firewall_master"]
        firewall_data_backup = network_data[tenant]["Firewall"]["Firewall_backup"]
        firewall_data_overview = network_data[tenant]["Firewall"]

        if firewall_data_master["status"]["internal_net_attach_status"] == "Completed" and firewall_data_backup["status"]["internal_net_attach_status"] == "Completed" and firewall_data_overview["status"]["re_route_to_fw_int_status"] == "Ready":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","ns_re_route.yml")
            namespace_tenant =  network_data[tenant]["namespace_tenant"]


            extra_vars = {'namespace_tenant': namespace_tenant   }

            command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
            sudo_password = "mmrj2023"

            for key, value in extra_vars.items():
                command.extend(['-e', f'{key}={value}'])
            
            firewall_data_overview["status"]["re_route_to_fw_int_status"] = "Running"  
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = process.communicate(sudo_password.encode())

            if process.returncode != 0:
                output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                firewall_data_overview["status"]["re_route_to_fw_int_status"] = "Ready"                
                print(f"Ansible playbook failed with error while creating table to re-route traffic :\n{output}")
            else:
                firewall_data_overview["status"]["re_route_to_fw_int_status"] = "Completed"
                print(f" create table to re-route traffic successfully created in {namespace_tenant}.")


        #execute vrrp in master
        if firewall_data_master["status"]["internal_net_attach_status"] == "Completed" and firewall_data_backup["status"]["internal_net_attach_status"] == "Completed" and firewall_data_master["status"]["vrrp_status"] == "Ready":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","vrrp.yml")
            namespace_tenant =  network_data[tenant]["namespace_tenant"]

            hostname = "FW1"
            router_id = 1
            vrrp_priority = 101
            state = "MASTER"
            src_dir = os.path.join(cwd , "templates")
            extra_vars = {'namespace_tenant': namespace_tenant,
              'hostname': hostname,
            'router_id': router_id,
             'vrrp_priority': vrrp_priority,
            'state': state,
            'src_dir' :src_dir   }
            

            command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
            sudo_password = "mmrj2023"

            for key, value in extra_vars.items():
                command.extend(['-e', f'{key}={value}'])
            
            firewall_data_master["status"]["vrrp_status"] = "Running"  
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = process.communicate(sudo_password.encode())

            if process.returncode != 0:
                output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                firewall_data_master["status"]["vrrp_status"] = "Ready"                
                print(f"Ansible playbook failed with error while doing VRRP configuration on Master Firewall :\n{output}")
            else:
                firewall_data_master["status"]["vrrp_status"] = "Completed"
                print(f"VRRP configuration on Master Firewall successfully created in {namespace_tenant}.")


        #execute vrrp in backup
        if firewall_data_master["status"]["internal_net_attach_status"] == "Completed" and firewall_data_backup["status"]["internal_net_attach_status"] == "Completed" and firewall_data_backup["status"]["vrrp_status"] == "Ready":
            inventory_path = os.path.join(cwd, "inventory.ini")
            playbook_path = os.path.join(cwd, "ansible_scripts","vrrp.yml")
            namespace_tenant =  network_data[tenant]["namespace_tenant"]

            hostname = "FW2"
            router_id = 2
            vrrp_priority = 100
            state = "BACKUP"
            src_dir = os.path.join(cwd , "templates")
            extra_vars = {'namespace_tenant': namespace_tenant,
              'hostname': hostname,
            'router_id': router_id,
             'vrrp_priority': vrrp_priority,
            'state': state ,
            'src_dir':src_dir  }

            command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]
            sudo_password = "mmrj2023"

            for key, value in extra_vars.items():
                command.extend(['-e', f'{key}={value}'])
            
            firewall_data_backup["status"]["vrrp_status"] = "Running"  
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = process.communicate(sudo_password.encode())

            if process.returncode != 0:
                output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')
                firewall_data_backup["status"]["vrrp_status"] = "Ready"                
                print(f"Ansible playbook failed with error while doing VRRP configuration on Backup Firewall :\n{output}")
            else:
                firewall_data_backup["status"]["vrrp_status"] = "Completed"
                print(f"VRRP configuration on Backup Firewall successfully created in {namespace_tenant}.")



with open(network_json_file_path, "w") as outfile:
    # write the JSON data to the file
    json.dump(network_data, outfile,indent=4)       
