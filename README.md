# FWaaS-VPC

FWaaS-VPC is the project which provides Firewall as a Service. The customers can create their networks in Virtual Provide Cloud by providing their requirements. The Customer Network is then built based on the requirements provided by customer. The Customer can also create Firewall policies for their Networks.

## Table of Contents

1. [Navigating through Repository](#navigating-through-repository)
   1. [North Bound](#north-bound)
   2. [South Bound](#south-bound)

2. [Build](#docker-build)
   1. [Prerequisites](#prerequisites)
   2. [Steps to Build](#steps-to-build)


## Navigating through Repository
This Repository has 2 folders. north_bound and south_bound.

### [North Bound](../master/north_bound)

#### createTenant.py

This Python file is used to create Tenant account for the customer. The Tenant Name and Tenant Code needs to be provided by the Customer. 

#### inputToplogy.json

This json file needs to be added with the VMs and Networks details that needs to be configured in the Customer Network. If any more networks or VMs need to be created at later point of time. The details need to be added in this file. So that infrastrure.json gets updated.

#### northBound.py

This python file is to populate the infrastructure.json in the folder Infrastructure. All the network related configuration given in the inputTopology.json is copied into the infrastructure.json with the Status.

#### firewallPolicies.csv

This csv file is to input the firewall policies that needs to be implemented in the Tenant Network.

#### firewallPolicies.py

Once the firewallPolicies.csv file is updated and this code is run it updates the infrastructure.json with the Firewall policies that are present in the firewallPolicies.csv file.


### [South Bound](../master/south_bound)

#### southBound.py

This python script utilizes the infrastructure.json in North Bound and builds the devices. This Script also updates the status of devices after execution in the infrastructure.json file.

#### vpc_setup.py

This python file is to create the public gateway for all the tenants so that the traffic can be routed outside of VPC to the Internet.


## Build

### Prerequisites

#### Linux

Linux system needs to be used to run this project. 

#### Python

Python Version in the system needs to be above 3.

#### Git

Git needs to be installed in the system to clone this repository to your linux system.


### Steps to Build

1) Run the createTenant.py in the North Bound directory and input the Tenant Name and Tenant Code.

2) Use this Tenant Name and Tenant Code to fill the inputTopology.json. Input the network configuration i.e, VMs and Networks and Firewall details that need to be created in the inputTopology.json.

3) Once the inputTopology.json is filled run the northBound.py and check if the given input file is valid.

4) Now go to the directory South Bound and run SouthBound.py. If the devices are created successfully the Status will be printed in the terminal.

5) Now fill the firewallPolicies.csv to implement the Firewall Policies in the Network.

6) Now run the firewallPolicies.py to check if firewallPolicies.csv is valid.

7) Now go to the directory South Bound and run SouthBound.py . This will implement the Firewall Policies and the Status will be printed in the terminal.









