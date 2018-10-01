import sys
from utils.html import HTMLElement
from logic.layout import OptimizeLayout
from logic.layout import SimpleWordListLayout
from logic.layout import GlossaryLayout
from logic.layout import SimpleWordTableLayout
from logic.layout import CodeletLayout
from logic.layout import CodeletCloudLayout
import logic.loadfile

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
  results = OptimizeLayout.optimize_layout_for_ratio(layout, name, groups[name])

  svg = HTMLElement('svg')
  width = 0
  height = 0
  for result in results:
    svg.add_child(result.html)
    if result.width > width:
      width = result.width
    if result.height > height:
      height = result.height

  svg.set_attr('width', width).set_attr('height', height)
  svg_outputs[name] = svg

# Output
########
for name in svg_outputs:
  fn = '{0}/{1}.svg'.format(output_path, name)
  with open(fn, 'w') as f:
    f.write(str(svg_outputs[name]))