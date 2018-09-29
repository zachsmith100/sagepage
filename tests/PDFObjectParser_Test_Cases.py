import sys
import os
from context import utils
from utils.pdf import *

class TestCase:
  def __init__(self):
    self.object = None

  def set_object(self, o):
    self.object = o

  def execute(self, expected_object, input_string):
    self.expected_object = expected_object
    parser = PDFObjectParser(self.set_object)
    reader = ParserReader()
    reader.read_string(parser.begin, input_string)

    if self.object is not None and str(self.object) == str(self.expected_object):
      print("PASS: expected '{0}' received '{1}'".format(self.expected_object, self.object))
      return True
    else:
      print("FAIL: expected '{0}' received '{1}'".format(self.expected_object, self.object))
    return False

test_case_params = []

obj = PDFObject()
obj.name = PDFValue(PDFValue.INT, 1)
obj.version = PDFValue(PDFValue.INT, 0)
obj.values.append(PDFValue(PDFValue.STRING, "test"))
input_string = "1 0 obj (test) endobj "
test_case_params.append((obj, input_string))

obj = PDFObject()
obj.name = PDFValue(PDFValue.INT, 2)
obj.version = PDFValue(PDFValue.INT, 0)
obj.values.append(PDFValue(PDFValue.DICTIONARY, {'key':PDFValue(PDFValue.NAME, 'value')}))
obj.stream_data = ['a', 's', 'd', 'f', ' ']
input_string = "2 0 obj <</key /value>> stream asdf endstream endobj "
test_case_params.append((obj, input_string))

obj = PDFObject()
obj.name = PDFValue(PDFValue.INT, 3)
obj.version = PDFValue(PDFValue.INT, 0)
obj.values.append(PDFValue(PDFValue.INT, 79))
input_string = "3 0 obj 79 endobj "
test_case_params.append((obj, input_string))

obj = PDFObject()
obj.name = PDFValue(PDFValue.INT, 4)
obj.version = PDFValue(PDFValue.INT, 0)
obj.values.append(PDFValue(PDFValue.DICTIONARY, {'key':PDFValue(PDFValue.NAME, 'value'), 'dict_test':PDFValue(PDFValue.DICTIONARY, {'tk0':PDFValue(PDFValue.INT, 101)})}))
obj.stream_data = ['a', 's', 'd', 'f', ' ']
input_string = "4 0 obj <</key /value /dict_test <</tk0 101 >> >> stream asdf endstream endobj "
test_case_params.append((obj, input_string))

obj = PDFObject()
obj.name = PDFValue(PDFValue.INT, 5)
obj.version = PDFValue(PDFValue.INT, 0)
d = {}
d['Type'] = PDFValue(PDFValue.NAME, "Page")
d['Parent'] = PDFValue(PDFValue.REFERENCE, PDFReference(PDFValue(PDFValue.INT, 1), PDFValue(PDFValue.INT, 0)))
a = [PDFValue(PDFValue.INT, 0), PDFValue(PDFValue.INT, 0), PDFValue(PDFValue.FLOAT, 595.275574), PDFValue(PDFValue.FLOAT, 841.889771)]
d['MediaBox'] = PDFValue(PDFValue.ARRAY, a)
d['Contents'] = PDFValue(PDFValue.REFERENCE, PDFReference(PDFValue(PDFValue.INT, 3), PDFValue(PDFValue.INT, 0)))
d2 = {}
d2['Type'] = PDFValue(PDFValue.NAME, 'Group')
d2['S'] = PDFValue(PDFValue.NAME, 'Transparency')
d2['I'] = PDFValue(PDFValue.BOOLEAN, 'true')
d2['CS'] = PDFValue(PDFValue.NAME, 'DeviceRGB')
d['Group'] = PDFValue(PDFValue.DICTIONARY, d2)
d['Resources'] = PDFValue(PDFValue.REFERENCE, PDFReference(PDFValue(PDFValue.INT, 2), PDFValue(PDFValue.INT, 0)))
obj.values.append(PDFValue(PDFValue.DICTIONARY, d))
input_string = """
5 0 obj
<< /Type /Page
   /Parent 1 0 R
   /MediaBox [ 0 0 595.275574 841.889771 ]
   /Contents 3 0 R
   /Group <<
      /Type /Group
      /S /Transparency
      /I true
      /CS /DeviceRGB
   >>
   /Resources 2 0 R
>>
endobj

"""
test_case_params.append((obj, input_string))

obj = PDFObject()
obj.name = PDFValue(PDFValue.INT, 9)
obj.version = PDFValue(PDFValue.INT, 0)
d = {}
d['Type'] = PDFValue(PDFValue.NAME, "XRef")
d['Length'] = PDFValue(PDFValue.INT, 50)
a = []
a.append(PDFValue(PDFValue.INT, 1))
a.append(PDFValue(PDFValue.INT, 3))
a.append(PDFValue(PDFValue.INT, 1))
d['W'] = PDFValue(PDFValue.ARRAY, a)
d['INFO'] = PDFValue(PDFValue.REFERENCE, PDFReference(PDFValue(PDFValue.INT, 3), PDFValue(PDFValue.INT, 0)))
d['Root'] = PDFValue(PDFValue.REFERENCE, PDFReference(PDFValue(PDFValue.INT, 2), PDFValue(PDFValue.INT, 0)))
d['Size'] = PDFValue(PDFValue.INT, 10)
a = []
a.append(PDFValue(PDFValue.HEXSTRING, '444b5072670d21a1ec33f8bc85d74b3f'))
a.append(PDFValue(PDFValue.HEXSTRING, 'b986190c72322b28310986f8e9343458'))
d['ID'] = PDFValue(PDFValue.ARRAY, a)
obj.values.append(PDFValue(PDFValue.DICTIONARY, d))
obj.stream_data = ['a', 's', 'd', 'f', ' ']
input_string = """
9 0 obj
<< /Type /XRef /Length 50 /W [ 1 3 1 ] /Info 3 0 R /Root 2 0 R /Size 10 /ID [<444b5072670d21a1ec33f8bc85d74b3f><b986190c72322b28310986f8e9343458>] >>
stream
asdf
endstream
endobj
"""
test_case_params.append((obj, input_string))

result = True
for params in test_case_params:
  test_case = TestCase()
  if test_case.execute(params[0], params[1]) != True:
    result = False


if result:
  print("PASSED")
else:
  print("FAILED")
