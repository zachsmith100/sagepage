import math

import csv
import sys
import json
import io
from logic.layout import OptimizeLayout
from logic.layout import SimpleWordListLayout
from logic.layout import GlossaryLayout
from logic.layout import SimpleWordTableLayout
from logic.layout import CodeletLayout
import logic.loadfile
from utils.permutations import ParamCombinationGenerator
from utils.permutations import OptimizableRange

################################################################################
# Command line
################################################################################
if len(sys.argv) != 4:
  print('Usage: %s <config.json> <links.csv> <output.svg>'
    % sys.argv[0], file=sys.stderr)
  exit(1)

config_path = sys.argv[1]
links_path = sys.argv[2]
output_path = sys.argv[3]

config = logic.loadfile.load_json(config_path)

groups = logic.loadfile.load_link_entries(links_path)

# Generate SVG
##############
svg_outputs = {}

for name in groups:
  constructor = globals()[config[name]['layout_class']]
  layout = constructor()
  layout.load_config(config[name])
  svg = OptimizeLayout.optimize_layout_for_ratio(layout, name, groups[name])
  svg_outputs[name] = str(svg)

# Output
########
for name in svg_outputs:
  fn = '{0}/{1}.svg'.format(output_path, name)
  with open(fn, 'w') as f:
    f.write(svg_outputs[name])