from utils.html import HTMLElement
from utils.html import HTMLStyleBuilder

class SVG:
  def dump_rects(filename, rects):
    width = 0
    height = 0
    for rect in rects:
      if (rect.x + rect.width) > width:
        width = rect.x + rect.width
      if (rect.y + rect.height) > height:
        height = rect.y + rect.height

    html = HTMLElement('svg')
    html.set_attr('x', str(0)).set_attr('y', str(0)).set_attr('width', str(width)).set_attr('height', str(height))

    for rect in rects:
      rect_element = HTMLElement('rect').set_attr('id', str(rect.identifier))
      rect_element.set_attr('x', str(rect.x)).set_attr('y', str(rect.y)).set_attr('width', str(rect.width)).set_attr('height', str(rect.height))
      style = HTMLStyleBuilder().set('fill', rect.get_color()).set('stroke', 'black').set('stroke-width', '1px')
      rect_element.set_attr('style', str(style))
      html.add_child(rect_element)

    with open(filename, 'w') as f:
      f.write(str(html))