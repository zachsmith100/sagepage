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
from logic.layout import SimpleImageLayout
from logic.layout import SimpleTextLineLayout
import logic.loadfile
from utils.permutations import ParamCombinationGenerator
from utils.permutations import OptimizableRange
from utils.models import Rect
from utils.rectarrange import Arrangeable
from utils.svg import SVG
from utils.html import HTMLElement
from utils.html import HTMLStyleBuilder
from utils.tree import BasicTree
from utils.configurable import Configurable

################################################################################
# Command line
################################################################################
if len(sys.argv) != 4:
  print('Usage: {0} <config.json> <links.csv> <output.svg>'.format(sys.argv[0]))
  exit(-1)

config_path = sys.argv[1]
links_path = sys.argv[2]
output_file = sys.argv[3]

################################################################################
# Load Config
################################################################################
class Group(BasicTree):
  def __init__(self):
    BasicTree.__init__(self)


config = logic.loadfile.load_json(config_path)
links = logic.loadfile.load_link_entries(links_path)

rect_svg_xref = {}
next_sort_group_id = 0

def load_links_group_svg(config, links_group_name, links_group):
  constructor = globals()[config['layout_class']]
  layout = constructor()
  Configurable.load_config(config, layout)
  svg_results = OptimizeLayout.optimize_layout_for_ratio(layout, links_group_name, links_group)
  return svg_results

def load_arrangeables(config, links, parent_arrangeable):
  global next_sort_group_id
  if 'links' in config:
    for links_group_name in config['links']:
      svg_results = load_links_group_svg(config['links'][links_group_name], links_group_name, links[links_group_name])
      rects = []
      for i in range(len(svg_results)):
        svg = svg_results[i]
        identifier = '{0}#{1}'.format(links_group_name, i)
        rect_svg_xref[identifier] = svg
        rect = Rect(identifier, 0, 0, svg.width, svg.height, 'gray', next_sort_group_id)
        next_sort_group_id = next_sort_group_id + 1
        rects.append(rect)
      child = parent_arrangeable.add_child(Arrangeable(links_group_name))
      child.add_rects(rects)

  if 'layout_groups' in config:
    for layout_group_name in config['layout_groups']:
      child = parent_arrangeable.add_child(Arrangeable(layout_group_name))
      load_arrangeables(config['layout_groups'][layout_group_name], links, child)

def adjust_xy(element, **kwargs):
  x = kwargs['x']
  y = kwargs['y']
  if 'x' in element.attributes:
    old_x = float(element.get_attr('x', 0))
    element.set_attr('x', str(x + old_x))
  if 'y' in element.attributes:
    old_y = float(element.get_attr('y', 0))
    element.set_attr('y', str(y + old_y))

root_arrangeable = Arrangeable('__root__')
load_arrangeables(config, links, root_arrangeable)

root_arrangeable.arrange()

width = 0
height = 0
for rect in root_arrangeable.get_rects():
  if (rect.x + rect.width) > width:
    width = rect.x + rect.width
  if (rect.y + rect.height) > height:
    height = rect.y + rect.height

html = HTMLElement('svg').set_attr('width', str(width)).set_attr('height', str(height))
html.set_attr('xmlns', 'http://www.w3.org/2000/svg')
html.set_attr('xmlns:xlink', 'http://www.w3.org/1999/xlink')

for rect in root_arrangeable.get_rects():
  svg = rect_svg_xref[rect.identifier]
  svg.html.iterate_children(adjust_xy, x=rect.x, y=rect.y)
  html.add_child(svg.html)

with open(output_file, 'w') as f:
  f.write(str(html))