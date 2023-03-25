import json

# create a dictionary to hold the JSON objects
json_data = {}

# define the initial object with the key "T1"
t1 = {
    "status": "false",
    "tenant_name": "",
    "tenant_code": ""
}

# add the initial object to the dictionary
json_data["T1"] = t1

# create 250 more objects by incrementing the key "T"
for i in range(2, 251):
    # create a new object with the incremented key
    key = "T" + str(i)
    new_obj = {
        "status": "false",
        "tenant_name": "",
        "tenant_code": ""
    }
    
    # add the new object to the dictionary
    json_data[key] = new_obj

# write the dictionary to a JSON file
with open("tenant_management.json", "w") as f:
    json.dump(json_data, f, indent=4)
