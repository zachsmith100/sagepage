import os
import re
import sys
import math
import csv
import html
import zlib
from html.parser import HTMLParser
from utils.pdf import PDF
from utils.pdf import PDFParser
from utils.pdf import ParserReader
from utils.pdf import PDFValue
from utils.pdf import PDFContentStreamParser
from utils.pdf import PDFWriter

################################################################################
# Command line
################################################################################
if len(sys.argv) != 3:
  print('Usage: %s <input-pdf> <output-pdf>'
    % sys.argv[0], file=sys.stderr)
  exit(1)

pdf_in_path = sys.argv[1]
pdf_out_path = sys.argv[2]

################################################################################
# Process PDF
################################################################################
print("Extracting objects from PDF...")
in_pdf = None

def set_pdf(pdf):
  global in_pdf
  in_pdf = pdf

parser = PDFParser(set_pdf)
reader = ParserReader()
if reader.read_file(parser.begin, pdf_in_path):
  print("SUCCESS")
else:
  print("FAIL")
  exit(-1)

for k in in_pdf.objects:
  obj = in_pdf.objects[k]
  decode_filter = None
  if 'Filter' in obj.named_values:
    decode_filter = obj.named_values['Filter']
  if decode_filter is not None and decode_filter.value == 'FlateDecode':
    decoded = zlib.decompress(obj.stream_data)
    obj.stream_data = decoded
    del obj.named_values['Filter']
    obj.named_values['Length'] = PDFValue(PDFValue.INT, len(obj.stream_data))

# Write PDF
###########
PDFWriter.write_file(in_pdf, pdf_out_path)

