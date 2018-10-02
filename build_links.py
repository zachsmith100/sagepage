import csv
import json
import sys
import logic.loadfile

class LinkEntry:
	def __init__(self, group_name, identifier, text, url):
		self.group_name = group_name
		self.identifier = identifier
		self.text = text
		self.url = url

	def __str__(self):
		return '{0} {1} {2} {3}'.format(self.group_name, self.identifier, self.text, self.url)

	def __repr__(self):
		return self.__str__()

################################################################################
# Command line
################################################################################
if len(sys.argv) != 4:
  print('Usage: %s <config.json> <links.csv> <output.csv>'
    % sys.argv[0], file=sys.stderr)
  exit(1)

config_path = sys.argv[1]
links_path = sys.argv[2]
output_file = sys.argv[3]

# Load JSON
###########
config = logic.loadfile.load_json(config_path)

# Load CSV
##########
links = {}

with open(links_path, 'r') as csv_file:
  csv_reader = csv.reader(csv_file)
  for link in csv_reader:
	  group_name = link[0]
	  if group_name not in links:
	  	links[group_name] = []
	  links[group_name].append(LinkEntry(link[0], link[1], link[2], link[3]))

config = logic.loadfile.load_json(config_path)

for key in config:
	for entry in links[key]:
		entry.url = '{0}{1}'.format(config[key]['base_url'], entry.url)
		print(entry.url)

# Write Assembled Links
#######################
with open(output_file, 'w') as csvfile:
    csv_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for group_name in links:
    	for entry in links[group_name]:
    		csv_writer.writerow([entry.group_name, entry.identifier, entry.text, entry.url])