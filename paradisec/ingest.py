'''
Created on 02/05/2013

@author: ilya
'''

import os
import shutil
import re
import xml.dom
import codecs

from hcsvlab_robochef.ingest_base import IngestBase
from hcsvlab_robochef.ingest_exception import IngestException
from hcsvlab_robochef import utils
from hcsvlab_robochef import metadata
from hcsvlab_robochef.annotations import *
from hcsvlab_robochef.utils.serialiser import *
from hcsvlab_robochef.utils.statistics import *
from hcsvlab_robochef.utils.filehandler import *

from xml.dom.minidom import parse, parseString
from xml.dom import Node
from xml.etree import ElementTree as ET

from rdf import paradisecMap


class ParadisecIngest(IngestBase):


  def ingestCorpus(self, srcdir, outdir):
    ''' This function will initiate the ingest process for the Auslit corpus '''
    
    print "  converting corpus in", srcdir, "into normalised data in", outdir
    print "    clearing and creating output location"
  
    self.clear_output_dir(outdir)

    print "    processing files..."
  
    files_to_process = self.__get_files(srcdir)
    total = len(files_to_process)
    sofar = 0
  
    for f in files_to_process:
      meta_dict = self.ingestDocument(srcdir, f)
      source_file = f
      f = f.replace(srcdir, outdir, 1)
      try:
        os.makedirs(os.path.dirname(f))
      except:
        pass
    
      ff = os.path.splitext(os.path.abspath(f))[0]
      
#      serialiser = Serialiser(os.path.dirname(ff))
#      serialiser.serialise_single(os.path.basename(ff), 'auslit', rawtext, body, paradisecMap, meta, annotations, source_file)
      serialiser = MetaSerialiser()
      serialiser.serialise(outdir, meta_dict['sampleid'], paradisecMap, meta_dict)
    
    
    sofar = sofar + 1
    print "\033[2K   ", sofar, "of", total, f, "\033[A"
    
    print "\033[2K   ", total, "files processed"


  def setMetaData(self, rcdir):
    ''' Loads the meta data for use during ingest '''
    pass


  def ingestDocument(self, srcdir, sourcepath):
    """ Read and process a corpus document """
  
    xml_tree = self.__load_xml_tree(sourcepath)
    
#    print ET.tostring(xml_tree)
    
#    meta = xml_tree.findall("metadata")
#    if (len(meta) != 1):
#      raise Exception("wrong number (" + str(len(meta)) + ") of metadata tags")

#    meta = metadata.xml2dict(xml_tree, ignore_root=True)
#    meta = self. __cleanse_meta(meta)
    meta = metadata.xml2tuplelist(xml_tree, ['olac', 'metadata'], True, False)
    meta_dict = self.__tuplelist2dict__(meta)
    meta_dict['sampleid'] = meta_dict['identifier']
    return meta_dict
#    meta['sampleid'] = os.path.basename(sourcepath)
  
    # Check to see if there is some additional meta data, if so grab some fields from there    
#    (meta_text, meta_tree) = self.__get_meta_tree(srcdir, os.path.basename(sourcepath))
#    if meta_tree is not None:
#      collection_elem = meta_tree.find('{http://austlit.edu.au/fulltext-metadata}collection')
#      if collection_elem is not None:
#        meta['collection'] = collection_elem.text
#  
#  
#    raw = xml_tree.findall("text")
#    if (len(raw) != 1):
#      raise Error("wrong number (" + str(len(raw)) + ") of text tags")
#  
#    cleansed_text = self.__cleanse_text(et.tostring(raw[0]).encode("utf-8"))
#  
#    return (text, self.__cleanse_meta(meta), cleansed_text, [])


  def __get_files(self, srcdir):
    ''' This function retrieves a list of files that the HCSvLab ingest should actually process '''
    filehandler = FileHandler()
    
    files = filehandler.getFiles(srcdir, r'^.+\.xml$')
    return_files = [os.path.join(srcdir, f) for f in files]
    return return_files


#  def __cleanse_meta(self, meta_dict):
#    clean = dict()
#    for k, v in meta_dict.items():
#      key = re.sub('\{.+?\}', '', k)
#      key = re.sub('olac_', '', key)
#      clean[key] = v.strip()
#    return clean
#      

  def __tuplelist2dict__(self, tuplelist):
    result = dict()
    for (k, v) in tuplelist:
      if k and v:
        result[k] = v
    return result

  def __load_xml_tree(self, sourcepath):
    '''
    This function reads in a XML docment as a text file and converts it into
    an XML tree for further processing
    '''
    
    fhandle = codecs.open(sourcepath, "r", "utf-8")
    text = fhandle.read()
    fhandle.close()
  
    text = text.replace('&ndash;', u"\u2013")
    text = text.replace('&mdash;', u"\u2014")
    text = text.replace('&copy;', u"\u00A9")
    text = text.replace('&ldquo;', u"\u201C")
    text = text.replace('&rdquo;', u"\u201D")
    text = text.replace('&emsp;', u"\u2003")
    text = text.replace('&eacute;', u"\u00E9")
    text = text.replace('&lsquo;', u"\u2018")
    text = text.replace('&rsquo;', u"\u2019")
    text = text.replace('&ecirc;', u"\u00EA")
    text = text.replace('&agrave;', u"\u00E0")
    text = text.replace('&egrave;', u"\u00E8")
    text = text.replace('&oelig;', u"\u0153")
    text = text.replace('&aelig;', u"\u00E6")
    text = text.replace('&hellip;', u"\u2026")
#    print sourcepath
    return ET.fromstring(text.encode("utf-8"))
#    return ET.fromstring(text)