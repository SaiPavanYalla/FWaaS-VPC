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




inventory_path = os.path.join(cwd, "inventory.ini")


#First step is to create networks
for tenant in  network_data:
    playbook_path = os.path.join(cwd, "ansible_scripts","create_ovs_bridge.yml")
    i=0
    for network in network_data[tenant]["Networks"]:
        
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
        
        i=i+1
            


    playbook_path = os.path.join(cwd, "ansible_scripts","create_vm.yml")
    j=0 
    for vm in network_data[tenant]["VMs"]:
        if vm["status"] == "Ready":

         
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
 
        j=j+1

    k=0
    playbook_path = os.path.join(cwd, "ansible_scripts","attach_ovs_bridge.yml")
    for vm in network_data[tenant]["VMs"]:
        if vm["status"] == "Completed":
            for connection in vm["connections"][0]["Connected_to"]:
                if vm["connection_status"][connection] == "Ready": 
                
                    for network in network_data[tenant]["Networks"]:
                        if connection == network["network_name"]:
                            if network["status"] == "Completed":
                            
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
                                    
                    

        k=k+1
                



with open(network_json_file_path, "w") as outfile:
    # write the JSON data to the file
    json.dump(network_data, outfile,indent=4)       
