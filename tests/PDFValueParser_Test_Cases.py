import sys
import os
from context import utils
from utils.pdf import *

class TestCase:
  def __init__(self):
    self.value = None

  def set_value(self, v):
    self.value = v

  def execute(self, expected_value, input_string):
    self.expected_value = expected_value
    parser = PDFValueParser(self.set_value)
    reader = ParserReader()
    reader.read_string(parser.begin, input_string)

    if self.value is not None and self.expected_value.type == self.value.type and self.expected_value.value == self.value.value:
      print("PASS: expected '{0}' received '{1}'".format(self.expected_value, self.value))
      return True
    else:
      print("FAIL: expected '{0}' received '{1}'".format(self.expected_value, self.value))
    return False


test_case_params = [
  (PDFValue(PDFValue.HEXSTRING, 'asdf'), "<asdf>"),
  (PDFValue(PDFValue.INT, 1), "1 %EOF"),
  (PDFValue(PDFValue.STRING, "test"), "(test) %EOF"),
  (PDFValue(PDFValue.ARRAY, [PDFValue(PDFValue.HEXSTRING, "444b5072670d21a1ec33f8bc85d74b3f"), PDFValue(PDFValue.HEXSTRING, "b986190c72322b28310986f8e9343458")]), "[<444b5072670d21a1ec33f8bc85d74b3f><b986190c72322b28310986f8e9343458>] "),
  (PDFValue(PDFValue.ARRAY, [PDFValue(PDFValue.REFERENCE, PDFReference(1,0)), PDFValue(PDFValue.REFERENCE, PDFReference(2,0)), PDFValue(PDFValue.REFERENCE, PDFReference(3,0))]), '[1 0 R 2 0 R 3 0 R] ')
]

result = True
for params in test_case_params:
  test_case = TestCase()
  if test_case.execute(params[0], params[1]) != True:
    result = False

if result:
  print("PASSED")
else:
  print("FAILED")
