import os
import json
import shutil
import ipaddress
import subprocess


inventory_path = os.path.join(cwd, "inventory.ini")

playbook_path = os.path.join(cwd, "ansible_scripts","create_pgw.yml")


command = ['sudo','ansible-playbook', playbook_path ,'-i', inventory_path]

sudo_password = "mmrj2023"


process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
stdout, stderr = process.communicate(sudo_password.encode())



if process.returncode != 0:
    output = stderr.decode('utf-8') if stderr else stdout.decode('utf-8')    
    print(f"Public Gateway creation failed with error:\n{output}")
else:
    print(f"Public Gateway creation successfull")
    