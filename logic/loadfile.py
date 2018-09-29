import json
import csv
from logic.layout import LinkEntry

# Load Links
############
def load_link_entries(links_csv_filename):
  groups = {}
  with open(links_csv_filename, 'r') as f: 
    csv_reader = csv.reader(f)
    for line in csv_reader:
      group_name = line[0].strip()
      identifier = line[1].strip()
      text = line[2].strip()
      url = line[3].strip()
      entry = LinkEntry(group_name, identifier, text, url)

      if group_name not in groups:
        groups[group_name] = []
      groups[group_name].append(entry)
  return groups

# Load Config
#############
def load_json(filename):
  config = {}
  with open(filename, 'r') as f:
    config = json.loads(f.read())
  return config