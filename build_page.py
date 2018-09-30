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
from utils.models import Rect
from utils.rectarrange import ArrangeRects
from utils.svg import SVG
from utils.html import HTMLElement
from utils.html import HTMLStyleBuilder

################################################################################
# Command line
################################################################################
if len(sys.argv) != 4:
  print('Usage: %s <config.json> <links.csv> <output.svg>'
    % sys.argv[0], file=sys.stderr)
  exit(1)

config_path = sys.argv[1]
links_path = sys.argv[2]
output_file = sys.argv[3]

config = logic.loadfile.load_json(config_path)

groups = logic.loadfile.load_link_entries(links_path)

# Generate SVG
##############
svg_outputs = {}

for group_name in groups:
  constructor = globals()[config[group_name]['layout_class']]
  layout = constructor()
  layout.load_config(config[group_name])
  svg = OptimizeLayout.optimize_layout_for_ratio(layout, group_name, groups[group_name])
  svg_outputs[group_name] = svg

# Assemble
##########
rects = []
for group_name in svg_outputs:
  svg = svg_outputs[group_name]
  rect = Rect(group_name, 0, 0, float(svg.get_attr('width', 0)), float(svg.get_attr('height',0)))
  rects.append(rect)

arrange_rects = ArrangeRects()
arrange_rects.arrange(rects, 1.618, '{0}.matrix.svg'.format(output_file))

width = 0
height = 0
for rect in rects:
  if (rect.x + rect.width) > width:
    width = rect.x + rect.width
  if (rect.y + rect.height) > height:
    height = rect.y + rect.height

html = HTMLElement('svg').set_attr('width', str(width)).set_attr('height', str(height))

for rect in rects:
  svg = svg_outputs[rect.identifier]
  svg.set_attr('x', str(rect.x)).set_attr('y', str(rect.y))
  html.add_child(svg)

with open(output_file, 'w') as f:
  f.write(str(html))