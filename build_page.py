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
from logic.layout import CodeletCloudLayout
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
def adjust_xy(element, **kwargs):
  print(kwargs)
  x = kwargs['x']
  y = kwargs['y']
  if 'x' in element.attributes:
    old_x = float(element.get_attr('x', 0))
    element.set_attr('x', str(x + old_x))
  if 'y' in element.attributes:
    old_y = float(element.get_attr('y', 0))
    element.set_attr('y', str(y + old_y))

def layout_sort_key(r):
  key = (r.sort_group << 28) + (r.width * r.height)
  return key

rect_svg_xref = {}
rects = []
next_sort_group_id = 0
for group_name in svg_outputs:
  for i in range(len(svg_outputs[group_name])):
    svg = svg_outputs[group_name][i]
    identifier = '{0}#{1}'.format(group_name, i)
    rect_svg_xref[identifier] = (group_name, i)
    rect = Rect(identifier, 0, 0, svg.width, svg.height, 'gray', next_sort_group_id)
    print(rect)
    next_sort_group_id = next_sort_group_id + 1
    rects.append(rect)

arrange_rects = ArrangeRects()
arrange_rects.arrange(rects, 1.618, layout_sort_key, '{0}.matrix.svg'.format(output_file))

width = 0
height = 0
for rect in rects:
  if (rect.x + rect.width) > width:
    width = rect.x + rect.width
  if (rect.y + rect.height) > height:
    height = rect.y + rect.height

html = HTMLElement('svg').set_attr('width', str(width)).set_attr('height', str(height))

for rect in rects:
  idx = rect_svg_xref[rect.identifier]
  group_name = idx[0]
  i = idx[1]
  svg = svg_outputs[group_name][i]
  print(rect)
  svg.html.iterate_children(adjust_xy, x=rect.x, y=rect.y)
  html.add_child(svg.html)

with open(output_file, 'w') as f:
  f.write(str(html))