import json
import os
import shutil
import ipaddress
import subprocess


    

# Open the JSON file
with open('tenant_management.json', 'r') as file:
    # Parse the JSON data
    tenant_data = json.load(file)



tenant_names = set()
for key, value in tenant_data.items():
        tenant_name = value["tenant_name"]
        if value["status"] == "true":
            tenant_names.add(tenant_name)

while True:

    # prompt the user for a tenant name and tenant code
    tenant_name = input("Enter tenant name: ")

    if tenant_name in tenant_names:
        print(f"Tenant name '{tenant_name}' is duplicated")
    else:
        break
        
        


    

tenant_code = input("Enter tenant code: ")


namespace =""


for i in range(1, 251):
    key = "T" + str(i)
    # create a new object with the incremented key
    if tenant_data[key]["status"] == "false":
        namespace = key
        tenant_data[key]["tenant_name"] = tenant_name
        tenant_data[key]["tenant_code"] = tenant_code
        tenant_data[key]["status"] = "true"
        break


    
# write the dictionary to a JSON file
with open("tenant_management.json", "w") as f:
    json.dump(tenant_data, f, indent=4)



cwd = os.getcwd()

parent_dir = os.path.dirname(cwd)


inventory_path = os.path.join(parent_dir,"south_bound", "inventory.ini")

playbook_path = os.path.join(parent_dir,"south_bound", "ansible_scripts","create_tenant.yml")

extra_vars = {'namespace_tenant': namespace   }


command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]

for key, value in extra_vars.items():
    command.extend(['-e', f'{key}={value}'])

sudo_password = "mmrj2023"


process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
stdout, stderr = process.communicate(sudo_password.encode())

if process.returncode != 0:
    output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')    
    print(f"Tenant creation failed with error:\n{output}")
else:
    print(f"Tenant creation successfull for "+ tenant_name)







