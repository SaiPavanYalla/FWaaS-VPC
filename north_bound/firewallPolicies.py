import csv

with open('firewallRequirements.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        print(row)
