import xml.etree.ElementTree as etree
import re

import sys

def write_metadata(d, xmlfile):
    """Generate our little XML metadata format
    from a dictionary of properties. Writes
    the XML to xmlfile.  Sorts by keys so we
    predict the output.
    """
    propel = etree.Element("properties")
    tree = etree.ElementTree(propel)
    wm(propel,d)
    tree.write(xmlfile, encoding="utf-8")

def wm(root, d):
  for key in sorted(d.iterkeys()):
    if isinstance(d[key], dict):
      subroot = etree.SubElement(root, "metadata", {"key": key})
      wm(subroot, d[key])
    else:
      etree.SubElement(root, "metadata", {"key": key, "value": d[key]})
      
def xml2dict(xml_tree, pre = "", ignore_root = False):
  d = {}
  key = pre+ (u"_" if (pre != "") else u"") + (xml_tree.tag.decode("utf-8"))
  if (len(list(xml_tree)) == 0):
    if key in d:
      key = key + "+"
    d[key] = (u"" if (xml_tree.text == None) else unicode(xml_tree.text))
  else:
    if (ignore_root):
      key = u""
    for tag in xml_tree:
      other = xml2dict(tag,key)
      for k in other:
        if k in d:
          k2 = k + "+"
        else:
          k2 = k
        d[k2] = other[k]
  return d


def xml2paradisecdict(xml_tree, ignorelist=[]):
  result = {}
  for node in xml_tree.iter():
    __strip_qual__(node)
    __flatten_attr__(node)
    if node.tag not in ignorelist:
      if node.text:
        if result.get(node.tag, False):
            result[node.tag].append(node.text.strip())
        else:
            result[node.tag] = [node.text.strip()]

  return result

def get_on_path(elts, d):
  """
  We sometimes want to recover particular elements which we encoded from xml by xml2dict, this method
  takes a list of strings giving the tag path to the element(s) in question and gives back a list of 
  values on such a path.  No regex, no attributes, nothing fancy
  >>> get_on_path(["one", "two"], {"one_two":"here", "one_two+": "there"})
  ['here', 'there']
  >>> get_on_path(["one", "two"], {"no":"nought","one_two":"here", "one_two+": "there"})
  ['here', 'there']
  """ 
  res = d.copy()
  for k in d:
    for i, e in enumerate(elts):
      ksplit = k.split("_") 
      if (i >= len(ksplit) or (ksplit[i]).rstrip("+") != elts[i]):
        del res[k]
        break
  return res.values()


def __strip_qual__(node):
#  print node.tag
  node.tag = re.sub('\{.+?\}', '', node.tag)
  for k,v in node.items():
    del node.attrib[k]
    key = re.sub('\{.+?\}', '', k)
    value = re.sub('\{.+?\}', '', v)
    if ':' in value:
      value = re.sub(r'.+?\:(.+)', r'\1', value)
    node.attrib[key] = value
  return node


def __flatten_attr__(node):
#this only works if strip_qual is true
  if 'type' in node.attrib:
    if 'code' in node.attrib:
      if node.text:
        node.tag = node.attrib['code']
      else:
        node.tag = node.attrib['type']
        node.text = node.attrib['code']
    elif node.text:
      node.tag = node.attrib['type']

  
import unittest  
import doctest    
def unittests():
  res = doctest.DocTestSuite()
  res.addTest(unittest.makeSuite(UnitTest))
  return res


class UnitTest(unittest.TestCase):
  def testTrivialXML2Dict(self):
    self.assertEqual(xml2dict(etree.fromstring("<root/>")), {"root":""})
    
  def testSimpleXML2Dict(self):
    e_tree = etree.fromstring("<one>hi</one>")
    self.assertEqual(xml2dict(e_tree), {"one":"hi"})

  def testSimplishXML2Dict(self):
    e_tree = etree.fromstring("<root><one>hi</one><two/><three></three><four><five>a</five></four></root>")
    self.assertEqual(xml2dict(e_tree), {"root_one":"hi", "root_two": "", "root_three": "", "root_four_five": "a"})

  def testIgnoreRoot(self):
    e_tree = etree.fromstring("<root><one>hi</one><two/><three></three><four><five>a</five></four></root>")
    self.assertEqual(xml2dict(e_tree, ignore_root= True), {"one":"hi", "two": "", "three": "", "four_five": "a"})

  def testDoubleUp(self):
    e_tree = etree.fromstring("<root><one><two>here</two></one><one><two>there</two></one></root>")
    self.assertEqual(xml2dict(e_tree, ignore_root=True), {"one_two": "here", "one_two+":"there"})

  def testTripleUp(self):
    e_tree = etree.fromstring("<root><one><two>here</two></one><one><two>there</two></one><one><two>everywhere</two></one></root>")
    self.assertEqual(xml2dict(e_tree, ignore_root=True), {"one_two": "here", "one_two+":"there", "one_two+": "everywhere"})
