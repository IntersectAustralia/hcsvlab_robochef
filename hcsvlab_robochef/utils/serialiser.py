import os
import shutil
import logging
import hcsvlab_robochef

from hcsvlab_robochef import metadata
from hcsvlab_robochef.rdf.map import RDF, AUSNC
from hcsvlab_robochef.utils.statistics import *
from hcsvlab_robochef.utils.parsing import *
from hcsvlab_robochef.upload.helper import *
from hcsvlab_robochef.rdf.serialiser import *


class Serialiser(object):

  configmanager.configinit()
  logger = logging.getLogger('parsers')
  
  def __init__(self, outdir):
    self.outdir = outdir
    
    if not os.path.exists(outdir):
        os.makedirs(outdir) 
  
  
  def serialise_single(self, sampleid, collection_name, rawtext, text, meta_map, meta_dict, ann_dict, document_identifier, source = None):
    '''
    This function generates the output files for a single textual source document. This function
    has been left behind for backwards compatibility
    '''
    self.__generate_rawtxt_output(sampleid, collection_name, rawtext, text, meta_map, meta_dict, source)
    return self.__serialise_dictionaries(sampleid, meta_map, meta_dict, ann_dict, document_identifier)


  def serialise_single_nontext(self, sampleid, collection_name, source, tipe, meta_map, meta_dict, ann_dict, document_identifier):
    '''
    This function generates the output files for a single textual source document. This function
    has been left behind for backwards compatibility (though the name has changed?)
    '''
    self.__generate_nontextual_output(sampleid, collection_name, source, tipe, meta_map, meta_dict)
    return self.__serialise_dictionaries(sampleid, meta_map, meta_dict, ann_dict, document_identifier)


  def serialise_multiple(self, sampleid, source_list, collection_name, meta_map, meta_dict, ann_dict, document_identifier):
    '''
    This function takes the source list of document and a dictionary of meta information and
    annotations and outputs rdf graphs.
    '''
    # We make a copy because we do not want the original to be modified
    new_meta_dict = meta_dict.copy()

    for source in source_list:
      # For each output source in a list generate the corresponding output, after which
      # generate the meta graphs and annotation graphs
      if source['filetype'] == 'Text':
        # Perform the normal function if the source type is TXT
        self.__generate_rawtxt_output(sampleid, 
                                      collection_name, 
                                      source['rawtext'], 
                                      source['text'], 
                                      meta_map, 
                                      new_meta_dict, 
                                      source['sourcepath'])
      else:
        self.__generate_nontextual_output(sampleid,
                                          collection_name, 
                                          source['sourcepath'], 
                                          source['filetype'], 
                                          meta_map, 
                                          new_meta_dict)

    return self.__serialise_dictionaries(sampleid, meta_map, new_meta_dict, ann_dict, document_identifier)

  def serialise_unique_multiple(self, sampleid, source_list, collection_name, meta_map, meta_dict, ann_dict, document_identifier):
    '''
    For LLC corpus
    This function takes the source list of document and a dictionary of meta information and
    annotations and outputs rdf graphs.
    '''
    # We make a copy because we do not want the original to be modified
    new_meta_dict = meta_dict.copy()

    for source in source_list:
      # For each output source in a list generate the corresponding output, after which
      # generate the meta graphs and annotation graphs
      self.__generate_unique_nontextual_output(source['keyname'],
                                               collection_name,
                                               source['sourcepath'],
                                               source['filetype'],
                                               meta_map,
                                               new_meta_dict)

    return self.__serialise_dictionaries(sampleid, meta_map, new_meta_dict, ann_dict, document_identifier)

  def __generate_nontextual_output(self, sampleid, collection_name, source, tipe, meta_map, meta_dict):
    '''
    If we are dealing with non-textual data then copy the required data over generating the meta information
    '''
    # Add source stats    
    doc_metadata = self.__gen_nontext_document_metadata(tipe, sampleid, source)
    key = 'table_document_' + doc_metadata['id'] + '#' + tipe

    add_to_dictionary(key, meta_dict, doc_metadata)

    # Copy the source document to the output folder
    shutil.copy2(source, self.outdir)

  def __generate_unique_nontextual_output(self, keyname, collection_name, source, tipe, meta_map, meta_dict):
    '''
    For LLC corpus
    If we are dealing with non-textual data then copy the required data over generating the meta information
    '''
    # Add source stats
    key = 'table_document_' + keyname

    meta_dict = add_to_dictionary(key,
                                  meta_dict,
                                  self.__gen_unique_nontext_document_metadata(tipe, keyname, source))

    # Copy the source document to the output folder
    shutil.copy2(source, os.path.join(self.outdir, keyname))

  def __generate_rawtxt_output(self, sampleid, collection_name, rawtext, text, meta_map, meta_dict, source):
    '''
    If we are dealing with raw text then serialise this raw text to disk
    '''
    if meta_dict is not None and len(meta_dict) > 0:
      # Add source stats
      stats = Statistics()
      
      if text != '' and text is not None:
        #print stats.get_sample_wordcount(text)
        meta_dict['itemwordcount'] = stats.get_sample_wordcount(text)
        meta_dict = add_to_dictionary('table_document_' + sampleid + '#Text',
                                      meta_dict,
                                      self.__gen_text_document_metadata(sampleid, 'Text', text))
                                        
                                        
      if rawtext != '' and rawtext is not None:
        meta_dict = add_to_dictionary('table_document_' + sampleid + '#Raw',
                                      meta_dict,
                                      self.__gen_text_document_metadata(sampleid, 'Raw', rawtext))
      
      if source:
        meta_dict = add_to_dictionary('table_document_' + sampleid + '#Original',
                                    meta_dict,
                                    self.__gen_nontext_document_metadata('Original', sampleid, source))
                                                                                            

    if rawtext:
      textfile = os.path.abspath(os.path.join(self.outdir, self.__get_text_file_name(sampleid, 'Raw')))
      texthandle = open(textfile, 'w')
      texthandle.write(rawtext.encode("utf-8"))
      texthandle.close()
       

    # write out content
    if text:
      txtfile = os.path.abspath(os.path.join(self.outdir, self.__get_text_file_name(sampleid, 'Text')))
      txthandle = open(txtfile, 'w')
      txthandle.write(text.encode("utf-8"))
      txthandle.close()

    if text and rawtext:
        self.__check_filesize_ratio(text, rawtext, sampleid, collection_name)

    # If there is also a source document copy this to the output directory
    if source:
      shutil.copy2(source, self.outdir)


  def __gen_nontext_document_metadata(self, tipe, sampleid, source):
    ''' Function adds document level meta data to the dictionary '''
    stats = Statistics()
    filename = os.path.basename(source)
    
    # 09/03/2012 SDP: The filelocation key has been removed. The Plone
    # service now determines the filelocation
    return {
      'filetype': tipe,
      'id' : filename,
      'documenttitle': filename,
      'filesize': stats.get_file_stats(source),
      'filename': filename
    }

  def __gen_unique_nontext_document_metadata(self, tipe, sampleid, source):
    '''
    For LLC corpus
    Function adds document level meta data to the dictionary
    '''
    stats = Statistics()

    sampleid = sampleid.replace(' ', '_')
    return {
      'filetype': tipe,
      'id' : self.__get_title(sampleid, tipe),
      'documenttitle': self.__get_title(sampleid, tipe),
      'filesize': stats.get_file_stats(source),
      'filename': sampleid
    }

  def __gen_text_document_metadata(self, sampleid, tipe, rawtext):
    ''' Function adds document level meta data to the dictionary '''
    stats = Statistics()
    
    # 09/03/2012 SDP: The filelocation key has been removed. The Plone
    # service now determines the filelocation
    return {
      'filetype': tipe,
      'id' : self.__get_title(sampleid, tipe),
      'documenttitle': self.__get_title(sampleid, tipe),
      'filesize': stats.get_item_stats(rawtext),
      'filename': self.__get_text_file_name(sampleid, tipe)
    }


  def __get_text_file_name(self, sampleid, tipe):
    if tipe == 'Raw':
      return sampleid + '-raw.txt'
      
    return sampleid + "-plain.txt"


  def __get_title(self, sampleid, tipe):
    return sampleid + '#' + tipe


  def __serialise_dictionaries(self, sampleid, meta_map, meta_dict, ann_dict, document_identifier):
    ''' 
    This function uses the Meta and Annotation serialiser to produce the RDF documents on disk.
    The serialised graphs are also returned to the caller.
    '''        
    meta_serialiser = MetaSerialiser()
    meta_graph = meta_serialiser.serialise(self.outdir, sampleid, meta_map, meta_dict, document_identifier)

    ann_serialiser = AnnotationSerialiser()
    ann_graph = ann_serialiser.serialise(self.outdir, sampleid, meta_map, ann_dict)
    
    return (meta_graph, ann_graph)

  def __check_filesize_ratio(self, plain_text, raw_text, sample_id, corpus):
    """
    Performs a sanity check to see if there is a massive difference between the raw text and plain
    text files, which might indicate that something has gone wrong in the parsing.
    """
    raw_plain_const = float(configmanager.get_config('C_' + corpus, 0))
    raw_plain_th_ratio = float(configmanager.get_config('TH_' + corpus, 0.3))

    plain_len = float(len(plain_text))
    raw_len = float(len(raw_text))
    ratio = plain_len / (raw_len - raw_plain_const)
    if plain_len > raw_len:
        self.logger.warn("%s: plain text longer than raw text warning (%d > %d): %s" % (corpus, plain_len, raw_len, sample_id))
    if ratio < raw_plain_th_ratio:
        self.logger.warn("%s: plain to raw ratio warning (%.2f < %.2f): %s" % (corpus, ratio, raw_plain_th_ratio, sample_id))
