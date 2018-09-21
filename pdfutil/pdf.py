import re
import zlib
import io

################################################################################
# PDF Parser
################################################################################


########
# Result
########
class Result:
  def __init__(self, error_msg=None, value=None):
    self.value = value
    self.error_msg = error_msg

  def is_error(self):
    if self.error_msg is None:
      return False
    return True

  def __str__(self):
    if self.error_msg is None:
      return "SUCCESS: {0}".format(str(self.value))
    return "ERROR: {0} {1}".format(self.error_msg, str(self.value))

  def __repr__(self):
    return self.__str__()

##########
# PDFUtils
##########
class PDFUtils:
  def is_special(s):
    if len(s) > 0 and s[0] in ['(', ')', '{', '}', '[', ']', '<', '>', '/', '%', '#']:
      return True
    return False

  def noop(dummy_0=None, dummy_1=None, dummy_2=None):
    pass

#####
# PDF
#####
class PDF:
  def __init__(self):
    self.header_line_1 = ''
    self.header_line_2 = ''
    self.objects = {}
    self.trailer = {}
    self.xref = None

  def get_next_obj_id(self):
    next_id = 1
    for key, obj in self.objects.items():
      if obj.name >= next_id:
        next_id = obj.name + 1
    return next_id

  def create_new_object(self):
    obj = PDFObject()
    obj.name = self.get_next_obj_id()
    self.objects[obj.get_key()] = obj
    self.trailer['Size'].value = len(self.objects)
    return obj

  def get_first_obj_id(self):
    first_id = -1
    for key, obj in self.objects.items():
      if first_id < 0 or first_id > obj.name:
        first_id = obj.name
    return first_id

  def get_obj_count(self):
    return len(self.objects)

  def __str__(self):
    obj_str = ''
    for k in self.objects:
      obj_str = "{0}{1}\n".format(obj_str, str(self.objects[k]))
    return "HEADER {0}\nOBJECTS:\n{1}\nXREF:\n{2}\nTRAILER:\n{3}".format(self.header_line_1, obj_str, self.xref, self.trailer)

  def __repr__(self):
    return self.__str__()

#########
# PDFXref
#########
class PDFXref:
  def __init__(self, initial_object_id=0, object_count=0):
    self.initial_object_id = initial_object_id
    self.object_count = object_count
    self.entries = []

  def __str__(self):
    return "initial ID: {0} obj count: {1} entries: {2}".format(self.initial_object_id, self.object_count, self.entries)

  def __repr__(self):
    return self.__str__()


##############
# PDFXrefEntry
##############
class PDFXrefEntry:
  def __init__(self, offset, generation, flag):
    self.offset = offset
    self.generation = generation
    self.flag = flag

  def __str__(self):
    return "OFFSET: {0} GEN: {1} FLAG: {2}".format(self.offset, self.generation, self.flag)

  def __repr__(self):
    return self.__str__()

##########
# PDFValue
##########
class PDFValue:
  ARRAY = 'array'
  INT = 'integer'
  FLOAT = 'float'
  STRING = 'string'
  HEXSTRING = 'hexstring'
  NAME = 'name'
  BOOLEAN = 'boolean'
  NULL = 'null'
  DICTIONARY = 'dictionary'
  ARRAY = 'array'
  REFERENCE = 'reference'
  TOKEN = 'token'
  
  def __init__(self, t, v):
    self.type = t
    self.value = v

  def default_value_str(self):
    s = ''
    if self.type == PDFValue.DICTIONARY:
      s = '<<{0}>>'.format(' '.join(['/{0} {1}'.format(k,v.default_value_str()) for k,v in self.value.items()]))
    elif self.type == PDFValue.ARRAY:
      s = '[{0}]'.format(' '.join([v.default_value_str() for v in self.value]))
    elif self.type == PDFValue.REFERENCE:
      s = "{0} {1} R".format(self.value.name, self.value.version)
    elif self.type == PDFValue.STRING:
      s = "({0})".format(self.value)
    elif self.type == PDFValue.HEXSTRING:
      s = '<{0}>'.format(self.value)
    elif self.type == PDFValue.NAME:
      s = '/{0}'.format(self.value)
    else:
      s = '{0}'.format(self.value)
    return s

  def __str__(self):
    display_value = self.value
    if self.type == PDFValue.BOOLEAN:
      if self.value:
        display_value = 'True'
      else:
        display_value = 'False'
    return "{0}({1})".format(self.type, display_value)

  def __repr__(self):
    return self.__str__()

##############
# PDFReference
##############
class PDFReference:
  def __init__(self, name, version):
    self.name = name
    self.version = version

  def get_key(self):
    return '{0}.{1}'.format(self.name, self.version)

  def __str__(self):
    return "name: {0} version: {1}".format(self.name, self.version)

  def __repr__(self):
    return self.__str__()

###########
# PDFObject
###########
class PDFObject:
  def __init__(self):
    self.comments = []
    self.name = 0
    self.version = 0
    self.named_values = {}
    self.values = []
    self.stream_data = []

  def get_ref(self):
    return PDFReference(self.name, self.version)

  def get_key(self):
    return '{0}.{1}'.format(self.name, self.version)

  def __str__(self):
    s = ("Object: {0} {1} Named Values: {2} Values: {3} Stream Len: {4}".format(self.name, self.version, self.named_values, self.values, len(self.stream_data)))
    return s

  def __repr__(self):
    return self.__str__()

#########################
# PDFContentStreamCommend
#########################
class PDFContentStreamCommand:
  def __init__(self, name, params=[]):
    self.name = name
    self.params = params

  def __str__(self):
    first = True
    out = ''
    last_param = None
    need_space_types = {PDFValue.INT, PDFValue.FLOAT, PDFValue.TOKEN, PDFValue.REFERENCE, PDFValue.NULL, PDFValue.NAME}
    for param in self.params:
      if first:
        first = False
      elif param.type in need_space_types or last_param.type in need_space_types:
        out = out + ' '
      out = out + param.default_value_str()
      last_param = param
    if last_param is not None and last_param.type in need_space_types:
      out = out + ' '
    out = out + self.name
    return out
    #return "{0} {1}".format(' '.join([param.default_value_str() for param in self.params]), self.name)

  def __repr__(self):
    return self.__str__()

################
# PDFParseResult
################
class PDFParseResult:
  def __init__(self, error_msg, peer_parse_func, next_parse_func, stream_bytes=None):
    self.error_msg = error_msg
    self.peer_parse_func = peer_parse_func
    self.next_parse_func = next_parse_func
    self.stream_bytes = stream_bytes

###############
# ParserBase
###############
class ParserBase:
  def __init__(self, set_value):
    self.set_value = set_value

##################
# PDFCommentParser
##################
class PDFCommentParser(ParserBase):
  def begin(self, b, n):
    if b == ord(' ') or b == ord('\t'):
      return PDFParseResult(None,None,self.begin)

    if b != ord('%'):
      return PDFParseResult("Expected char code {0}, received char code {1}".format(ord('%'), ord(b)),None,None)

    self.line = []
    return PDFParseResult(None,None,self.read)

  def read(self, b, n):
    if chr(b) == '\n':
      self.set_value(self.line)
      return PDFParseResult(None,None,None)

    self.line.append(b)
    return PDFParseResult(None,None,self.read)

################
# PDFTokenParser
################
class PDFTokenParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.token = []

  def set_token(self):
    self.set_value(''.join(self.token))

  def begin(self, b, n):
    if str(chr(b)).isspace():
      return PDFParseResult(None, None, self.begin)
    return PDFParseResult(None, self.read, None)

  def read(self, b, n):
    if str(chr(b)).isspace():
      self.set_token()
      return PDFParseResult(None, None, None, [b])

    if PDFUtils.is_special(str(chr(b))):
      if len(self.token) == 0:
        if chr(b) == '<':
          self.token.append('<')
          return PDFParseResult(None, None, self.check_dictionary_begin)
        elif chr(b) == '>':
          self.token.append('>')
          return PDFParseResult(None, None, self.check_dictionary_end)
        else:
          self.token.append(chr(b))
          self.set_token()
          return PDFParseResult(None, None, None)
      self.set_token()
      return PDFParseResult(None, None, None, [b])

    self.token.append(chr(b))
    return PDFParseResult(None, None, self.read)

  def check_dictionary_begin(self, b, n):
    if chr(b) == '<':
      self.token.append('<')
      self.set_token()
      return PDFParseResult(None, None, None)
    self.set_token()
    return PDFParseResult(None, None, None, [b])

  def check_dictionary_end(self, b, n):
    if chr(b) == '>':
      self.token.append('>')
      self.set_token()
      return PDFParseResult(None, None, None)
    self.set_token()
    return PDFParseResult(None, None, None, [b])

################
# PDFArrayParser
################
class PDFArrayParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.array = []
    self.last_token = None

  def append_array_value(self, v):
    self.array.append(v)
    if v.type == PDFValue.TOKEN:
      self.last_token = v

  def begin(self, b, n):
    if str(chr(b)).isspace():
      return PDFParseResult(None, None, self.begin)
    if chr(b) != '[':
      return PDFParseResult("Array parsing expected '[' as first char but received '{0}'.".format(chr(b)), None, None)
    return PDFParseResult(None, None, self.read_value)

  def read_value(self, b, n):
    if self.last_token is not None and self.last_token.value == ']':
      self.array.pop()
      self.set_value(PDFValue(PDFValue.ARRAY, self.array))
      return PDFParseResult(None, None, None, [b])
    return PDFParseResult(None, PDFValueParser(self.append_array_value).begin, self.read_value)

#################
# PDFStringParser
#################
class PDFStringParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.stack = []
    self.escaped = False
    self.string = []

  def begin(self, b, n):
    if str(chr(b)).isspace():
      return PDFParseResult(None, None, self.begin)

    if chr(b) == '(':
      self.stack.append('(')
      return PDFParseResult(None, None, self.read)
    return PDFParseResult("Expected '(', received '{0}'".format(chr(b)), None, None)

  def read(self, b, n):
    if self.escaped is True:
      self.escaped = False
      self.string.append(chr(b))      
      return PDFParseResult(None, None, self.read)
    
    if chr(b) == '\\':
      self.escaped = True
      self.string.append(chr(b))
      return PDFParseResult(None, None, self.read)

    if chr(b) == '(':
      self.stack.append('(')
      self.string.append('(')
      return PDFParseResult(None, None, self.read)
    
    if chr(b) == ')':
      self.stack.pop()
      if len(self.stack) < 1:
        self.set_value(PDFValue(PDFValue.STRING, ''.join(self.string)))
        return PDFParseResult(None, None, None)
      else:
        self.string.append(')')
        return PDFParseResult(None, None, self.read)

    self.string.append(chr(b))
    return PDFParseResult(None, None, self.read)
    

################
# PDFValueParser
################
class PDFValueParser(ParserBase):
  def set_token(self, t):
    self.token = t

  def set_hex_string(self, s):
    self.set_value(PDFValue(PDFValue.HEXSTRING, s))

  def set_array(self, a):
    self.set_value(a)

  def set_string(self, s):
    self.set_value(s)

  def create_value_from_token(self, t):
    value = None
    if PDFUtils.is_special(self.token):
      value = PDFValue(PDFValue.TOKEN, self.token)
    elif re.match(r'^[\+-]?\d+\.\d+$', self.token) is not None:
      value = PDFValue(PDFValue.FLOAT, float(self.token))
    elif re.match('^[\+-]?\d+$', self.token) is not None:
      value = PDFValue(PDFValue.INT, int(self.token))
    elif re.match('^true$|^false$', self.token) is not None:
      value = PDFValue(PDFValue.BOOLEAN, bool(self.token))
    elif re.match('^null$', self.token) is not None:
      value = PDFValue(PDFValue.NULL, None)
    else:
      value = PDFValue(PDFValue.TOKEN, self.token)
    return value

  def begin(self, b, n):
    return PDFParseResult(None, PDFTokenParser(self.set_token).begin, self.initial_token_complete)

  def initial_token_complete(self, b, n):
    value = self.create_value_from_token(self.token)
    if value is None:
      return PDFParseResult("Unsupported value format for value '{0}' (length={1})".format(self.token, len(self.token)), None, None)
    if value.type == PDFValue.TOKEN:
      if value.value == '<<':
        return PDFParseResult(None, None, PDFDictionaryParser(self.set_value).begin, bytes('<<{0}'.format(chr(b)).encode()))
      elif value.value == '<':
        return PDFParseResult(None, PDFTokenParser(self.set_hex_string).begin, self.verify_hex_string_close)
      elif value.value == '(':
        return PDFParseResult(None, None, PDFStringParser(self.set_string).begin, '({0}'.format(chr(b)).encode())
      elif value.value == '[':
        return PDFParseResult(None, None, PDFArrayParser(self.set_array).begin, '[{0}'.format(chr(b)).encode())
      elif value.value == '/':
        return PDFParseResult(None, PDFTokenParser(self.set_token).begin, self.process_name_token)
    if value.type == PDFValue.INT and str(chr(b)).isspace():
      self.reference_value_1 = value
      return PDFParseResult(None, PDFTokenParser(self.set_token).begin, self.check_reference_value_2)
    self.set_value(value)
    return PDFParseResult(None, None, None, [b])

  def verify_hex_string_close(self, b, n):
    if chr(b) == '>':
      return PDFParseResult(None, None, None)
    return PDFParseResult("Expected '>', received '{0}'".format(chr(b)))

  def process_name_token(self, b, n):
    self.set_value(PDFValue(PDFValue.NAME, self.token))
    return PDFParseResult(None, None, None, [b])

  def check_reference_value_2(self, b, n):
    value = self.create_value_from_token(self.token)
    if value.type == PDFValue.INT and str(chr(b)).isspace():
      self.reference_value_2 = value
      return PDFParseResult(None, PDFTokenParser(self.set_token).begin, self.check_reference_value_3)
    self.set_value(self.reference_value_1)
    push_back = bytearray(str.encode(self.token))
    push_back.extend(' '.encode())
    push_back.extend([b])
    return PDFParseResult(None, None, None, push_back)
    
  def check_reference_value_3(self, b, n):
    if self.token == 'R':
      self.set_value(PDFValue(PDFValue.REFERENCE, PDFReference(self.reference_value_1.value, self.reference_value_2.value)))
      return PDFParseResult(None, None, None, [b])
    self.set_value(self.reference_value_1)

    push_back = []
    push_back.extend(bytearray(str(self.reference_value_2.value).encode()))
    push_back.extend(' '.encode())
    push_back.extend(self.token.encode())
    push_back.extend(' '.encode())
    push_back.extend([b])
    return PDFParseResult(None, None, None, push_back)
    

#####################
# PDFDictionaryParser
#####################
class PDFDictionaryParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.dictionary = {}
    self.name_token = None
    self.open_token = None

  def set_name_token(self, t):
    self.name_token = t

  def set_open_token(self, t):
    self.open_token = t

  def set_dictionary_value(self, v):
    self.dictionary[self.name_token.value] = v

  def reset(self,name_token):
    self.name_token = name_token
    self.value_tokens = None
    if name_token is None:
      return PDFParseResult(None, self.begin, None)
    return PDFParseResult(None, self.verify_name_token, None)

  def begin(self, b, n):
    if str(chr(b)).isspace():
      return PDFParseResult(None, None, self.begin)
    return PDFParseResult(None,PDFTokenParser(self.set_open_token).begin, self.verify_open_token)

  def verify_open_token(self, b, n):
    if self.open_token == None or self.open_token != '<<':
      return PDFParseResult("Expected '<<', received '{0}'".format(self.open_token), None, None)
    return PDFParseResult(None, self.read_name, None)

  def read_name(self, b, n):
    return PDFParseResult(None, PDFValueParser(self.set_name_token).begin, self.verify_name_token)

  def verify_name_token(self, b, n):
    if self.name_token.type == PDFValue.NAME:
      return PDFParseResult(None, self.read_value, None) 
    if self.name_token.type == PDFValue.TOKEN and self.name_token.value == '>>':
      self.set_value(PDFValue(PDFValue.DICTIONARY, self.dictionary))
      return PDFParseResult(None, None, None)
    return PDFParseResult("Dictionary missing name entry (expected name, found '{0}' instead).".format(self.name_token), None, None)

  def read_value(self, b, n):
    return PDFParseResult(None,PDFValueParser(self.set_dictionary_value).begin, self.read_name)

#################
# PDFStreamParser
#################
class PDFStreamParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.stream = []
    self.end_token = "endstream"
    self.end_token_pos = 0

  def begin(self, b, n):
    if str(chr(b)).isspace():
      return PDFParseResult(None, None, self.begin)
    return PDFParseResult(None, self.read, None)

  def read(self, b, n):
    self.stream.append(b)
    if chr(b) == self.end_token[self.end_token_pos]:
      self.end_token_pos += 1
      return PDFParseResult(None, self.verify_token_state, None)
    else:
      self.end_token_pos = 0
    return PDFParseResult(None, None, self.read)

  def verify_token_state(self, b, n):
    if self.end_token_pos == len(self.end_token):
      input_stream = bytes(self.stream[:len(self.stream)-(len(self.end_token) + 1)])
      self.set_value(input_stream)
      return PDFParseResult(None,None,None)
    return PDFParseResult(None, None, self.read)
    
    
#################
# PDFObjectParser
#################
class PDFObjectParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.obj = PDFObject()
    self.last_token = ''
    self.name = None
    self.version = None

  def set_comment(self, v):
    self.obj.comments.append(''.join(v))

  def set_name(self, name):
    self.name = name

  def set_version(self, version):
    self.version = version

  def set_obj_tag(self, t):
    self.obj_tag = t

  def set_last_token(self, t):
    self.last_token = t

  def append_value(self, v):
    if v.type == PDFValue.TOKEN:
      self.last_token = v.value
    elif v.type == PDFValue.DICTIONARY:
      self.obj.named_values.update(v.value)
    else:
      self.obj.values.append(v)

  def set_stream_data(self, d):
    self.obj.stream_data = d

  def begin(self, b, n):
    if str(chr(b)).isspace():
      return PDFParseResult(None, None, self.begin)
    if chr(b) == '%':
      return PDFParseResult(None,PDFCommentParser(self.set_comment).begin, self.begin)
    return PDFParseResult(None, self.read_name, None)

  def read_name(self, b, n):
    return PDFParseResult(None,PDFValueParser(self.set_name).begin, self.verify_name)

  def verify_name(self, b, n):
    if self.name.type != PDFValue.INT:
      return PDFParseResult("Expected int name, but received '{0}'".format(self.obj.name.value), None, None)
    self.obj.name = self.name.value
    return PDFParseResult(None, PDFValueParser(self.set_version).begin, self.verify_version)

  def verify_version(self, b, n):
    if self.version.type != PDFValue.INT:
      return PDFParseResult("Expected int version, but received '{0}'".format(self.version), None, None)
    self.obj.version = self.version.value
    return PDFParseResult(None, PDFValueParser(self.set_obj_tag).begin, self.verify_obj_tag)

  def verify_obj_tag(self, b, n):
    if self.obj_tag.type != PDFValue.TOKEN:
      return PDFParseResult("Expected 'obj' tag, but received '{0}'".format(self.obj_tag), None, None)
    return PDFParseResult(None,PDFValueParser(self.append_value).begin, self.read_value)

  def read_value(self, b, n):
    return PDFParseResult(None,PDFValueParser(self.append_value).begin, self.process_value)

  def process_value(self, b, n):
    if self.last_token.lower() == 'stream':
      return PDFParseResult(None, PDFStreamParser(self.set_stream_data).begin, self.read_value)
    if self.last_token.lower() == 'endobj':
      self.set_value(self.obj)
      return PDFParseResult(None, None, None, [b])
    return PDFParseResult(None, self.read_value, None)

##################
# PDFTrailerParser
##################
class PDFTrailerParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.dictionary = {}

  def set_open_token(self, t):
    self.open_token = t

  def set_trailer(self, t):
    self.set_value(t.value)
    
  def begin(self, b, n):
    return PDFParseResult(None, PDFTokenParser(self.set_open_token).begin, self.verify_open_token)

  def verify_open_token(self, b, n):
    if self.open_token == None or self.open_token.lower() != 'trailer':
      return PDFParseResult("Expected token 'trailer' but received '{0}'".format(self.open_token))
    return PDFParseResult(None, self.read, None)

  def read(self, b, n):
    return PDFParseResult(None, PDFValueParser(self.set_trailer).begin, None)

####################
# PDFXrefEntryParser
####################
class PDFXrefEntryParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.offset = None
    self.generation = None
    self.flag = None

  def set_offset(self, i):
    self.offset = i

  def set_generation(self, g):
    self.generation = g

  def set_flag(self, f):
    self.flag = f

  def begin(self, b, n):
    return PDFParseResult(None, PDFValueParser(self.set_offset).begin, self.read_generation)

  def read_generation(self, b, n):
    return PDFParseResult(None, PDFValueParser(self.set_generation).begin, self.read_flag)

  def read_flag(self, b, n):
    return PDFParseResult(None, PDFValueParser(self.set_flag).begin, self.verify_entry)

  def verify_entry(self, b, n):
    if self.offset is None or self.generation is None or self.flag is None:
      return PDFParseResult("PDF xref entry expected (invalid format; offset={0} generation={1} flag={2})".format(self.offset, self.generation, self.flag), None, None)
    self.set_value(PDFXrefEntry(self.offset.value, self.generation.value, self.flag.value))
    return PDFParseResult(None, None, None, [b])

##################
# PDFXRefParser
##################
class PDFXrefParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.xref = PDFXref()
    self.open_token = None

  def set_open_token(self, t):
    self.open_token = t

  def set_initial_id(self, v):
    self.xref.initial_object_id = v.value

  def set_obj_count(self, v):
    self.xref.object_count = v.value

  def append_entry(self, e):
    self.xref.entries.append(e)

  def begin(self, b, n):
    return PDFParseResult(None, PDFTokenParser(self.set_open_token).begin, self.verify_open_token)

  def verify_open_token(self, b, n):
    #if self.open_token == None or self.open_token.lower() != 'xref':
      #return PDFParseResult("Expected token 'xref' but received '{0}'".format(self.open_token), None, None)
    return PDFParseResult(None, self.read_start_index, None)

  def read_start_index(self, b, n):
    return PDFParseResult(None, PDFValueParser(self.set_initial_id).begin, self.read_obj_count)

  def read_obj_count(self, b, n):
    return PDFParseResult(None, PDFValueParser(self.set_obj_count).begin, self.read_entry)

  def read_entry(self, b, n):
    if len(self.xref.entries) == self.xref.object_count:
      self.set_value(self.xref)
      return PDFParseResult(None, None, None)
    return PDFParseResult(None, PDFXrefEntryParser(self.append_entry).begin, self.read_entry)

####################
# PDFStartXrefParser
####################
class PDFStartXrefParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.index = None

  def set_open_token(self, t):
    self.open_token = t

  def set_index(self, i):
    self.index = i

  def begin(self, b, n):
    return PDFParseResult(None, PDFTokenParser(self.set_open_token).begin, self.verify_open_token)

  def verify_open_token(self, b, n):
    if self.open_token == None or self.open_token.lower() != 'startxref':
      return PDFParseResult("Expected token 'startxref' but received '{0}'".format(self.open_token))
    return PDFParseResult(None, self.read, None)

  def read(self, b, n):
    return PDFParseResult(None, PDFValueParser(self.set_index).begin, self.verify_value)

  def verify_value(self, b, n):
    if self.index is None:
      return PDFParseResult("Expected integer index, received 'None'", None, None)
    if self.index.type != PDFValue.INT:
      return PDFParseResult("Expected integer index, received token of type '{0}'".format(self.index.type))
    return PDFParseResult(None, None, None, [b])

############
# PDF Parser
############
class PDFParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.pdf = PDF()

  def set_header_line_1(self, v):
    self.pdf.header_line_1 = v

  def set_header_line_2(self, v):
    self.pdf.header_line_2 = v

  def set_last_value(self, v):
    self.last_value = v

  def append_object(self, o):
    self.pdf.objects[o.get_key()] = o

  def set_trailer(self, t):
    self.pdf.trailer = t

  def set_start_xref(self, n):
    pass

  def set_xref(self, x):
    self.pdf.xref = x

  def begin(self, b, n):
    return PDFParseResult(None,PDFCommentParser(self.set_header_line_1).begin, self.begin_header_line_2)

  def begin_header_line_2(self, b, n):
    if b == ord('%'):
      return PDFParseResult(None,PDFCommentParser(self.set_header_line_2).begin, self.begin_object)
    return PDFParseResult(None, self.begin_object, None)

  def begin_object(self, b, n):
    if str(chr(b)).isspace():
      return PDFParseResult(None, None, self.begin_object)
    if chr(b) == 'x': #xref
      return PDFParseResult(None, PDFXrefParser(self.set_xref).begin, self.begin_object)
    if chr(b) == 's': #startxref
      return PDFParseResult(None, PDFStartXrefParser(self.set_start_xref).begin, self.complete)
    if chr(b) == 't': #trailer
      return PDFParseResult(None, PDFTrailerParser(self.set_trailer).begin, self.begin_object)
    return PDFParseResult(None, PDFObjectParser(self.append_object).begin, self.begin_object)
   
  def complete(self, b, n):
    self.set_value(self.pdf)
    return PDFParseResult(None, None, None)

########################
# PDFContentStreamParser
########################
class PDFContentStreamParser(ParserBase):
  def __init__(self, set_value):
    ParserBase.__init__(self, set_value)
    self.current_params = []

  def append_value(self, value):
    if value.type == PDFValue.TOKEN:
      cmd = PDFContentStreamCommand(value.value, self.current_params)
      self.current_params = []
      self.set_value(cmd)
    else:
      self.current_params.append(value)
  
  def begin(self, b, n):
    return PDFParseResult(None, PDFValueParser(self.append_value).begin, self.begin)


##############
# ParserReader
##############
class ParserReader:
  def __init__(self):
    pass

  def set_pdf(self, pdf):
    self.pdf = pdf


  def read_string(self, parser, input_string):
    result = False
    with io.BytesIO(bytearray(input_string.encode())) as reader:
      result = self.parse(parser, reader)
    return result


  def read_file(self, parser, filename):
    result = False
    with open(filename, 'rb') as f:
      result = self.parse(parser, f)
    return result

  def parse(self, parser, reader):
    stack = []
    stack.append(parser)
    brk = False

    next_byte_index = 0
    bytes = []
    bytes_read = 0
    next_parser = stack.pop()

    b = reader.read(1)

    if b != b"":
      bytes.append(b[0])

    while bytes_read < len(bytes):
      if next_parser is None:
        break
 
      next_byte = bytes[bytes_read]
      
      if brk is True:
        print("brk: {0} {1} {2}".format(bytes_read, chr(next_byte), bytes))

      bytes_read += 1

      peer_parser = next_parser
     
      while peer_parser is not None:
        #print("byte: {0} byte_index: {1} f: {2}".format(chr(next_byte), next_byte_index, peer_parser.__qualname__))
        result = peer_parser(next_byte, next_byte_index)

        if result.error_msg is not None:
          print("{0}: byte: {1} byte_index: {2} message: {3}".format(peer_parser.__qualname__, next_byte, next_byte_index, result.error_msg))
          return False

        if result.next_parse_func is not None:
          stack.append(result.next_parse_func)
        
        peer_parser = result.peer_parse_func
    
      if result.stream_bytes is not None:
        stream = []
        stream.extend(result.stream_bytes)
        stream.extend(bytes[bytes_read:])
        bytes = stream
        bytes_read = 0
      elif bytes_read == len(bytes):
        bytes = []
        bytes_read = 0
        b = reader.read(1)
        if b != b"":
          bytes.append(b[0])
          next_byte_index += 1
  
      next_parser = None

      if len(stack) > 0:
        next_parser = stack.pop()

    return True


################
# PDFWriterUtils
################
class PDFWriterUtils:
  def write_header(pdf, output_file):
    line_1 = ''.join([chr(b) for b in pdf.header_line_1])
    line_1 = "%{0}\n".format(line_1)
    output_file.write(line_1.encode())
    if len(pdf.header_line_2) > 0:
      output_file.write(bytes('%'.encode()))
      output_file.write(bytes(pdf.header_line_2))
      output_file.write("\n".encode())

  def write_value(v, f):  
    s = v.default_value_str()    
    f.write(s.encode())

  def write_object(obj, output_file):
    begin_obj = "{0} {1} obj\n".format(obj.name, obj.version).encode()
    output_file.write(begin_obj)

    if len(obj.named_values) > 0:
      named_values = PDFValue(PDFValue.DICTIONARY, obj.named_values)
      PDFWriterUtils.write_value(named_values, output_file)
      output_file.write("\n".encode())

    if len(obj.values) > 0:
      first = True
      for value in obj.values:
        if first:
          first = False
        else:
          output_file.write(' '.encode())
        PDFWriterUtils.write_value(value, output_file)
      output_file.write("\n".encode())  

    if len(obj.stream_data) > 0:
      output_file.write("stream\n".encode())
      output_file.write(bytes(obj.stream_data))
      output_file.write("\nendstream\n".encode())
    output_file.write("endobj\n".encode())

  def write_xref(pdf, xref_indexes, output_file):
    output_file.write("xref\n".encode())
    output_file.write("{0} {1}\n".format(0, pdf.get_obj_count()+1).encode())
    output_file.write("0000000000 65535 f\n".encode())

    keys = [k for k in xref_indexes.keys()]
    keys.sort()

    for key in keys:
      output_file.write("{:0>10d} {:0>5d} n\n".format(xref_indexes[key], 0).encode())

  def write_footer(pdf, xref_indexes, output_file):
    start_xref = output_file.tell()
    PDFWriterUtils.write_xref(pdf, xref_indexes, output_file)
    output_file.write("trailer\n".encode())
    PDFWriterUtils.write_value(PDFValue(PDFValue.DICTIONARY, pdf.trailer), output_file)
    output_file.write("\nstartxref\n".encode())
    output_file.write("{0}\n".format(start_xref).encode())
    output_file.write("%%EOF".encode())

###########
# PDFWriter
###########
class PDFWriter:
  def write_file(pdf, filename):
    with open(filename, "wb") as f:
      xref_indexes = {}
      PDFWriterUtils.write_header(pdf, f)
      for key, obj in pdf.objects.items():
        xref_indexes[obj.get_key()] = f.tell()
        PDFWriterUtils.write_object(obj, f)
      PDFWriterUtils.write_footer(pdf, xref_indexes, f)










































