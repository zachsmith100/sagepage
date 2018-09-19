import sys
import os
sys.path.append(os.path.abspath(".."))
from pdf import *

class TestCase:
  def __init__(self):
    self.token = None

  def set_token(self, t):
    self.token = t

  def execute(self, expected_token, input_string):
    self.expected_token = expected_token
    parser = PDFTokenParser(self.set_token)
    reader = ParserReader()
    reader.read_string(parser.begin, input_string)

    if self.token is not None and self.expected_token == self.token:
      print("PASS: expected '{0}' received '{1}'".format(self.expected_token, self.token))
      return True
    else:
      print("FAIL: expected '{0}' received '{1}'".format(self.expected_token, self.token))
    return False


test_case_params = [
  ('<<', "<<"),
  ('<', "< "),
  ('[', '[asdf'),
  ('(', '(adf'),
  ('asdf', 'asdf>')
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
