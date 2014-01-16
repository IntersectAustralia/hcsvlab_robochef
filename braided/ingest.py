import doctest
import subprocess
import pprint
import sys
import os
import shutil
import string
import re

from pyparsing import *
from hcsvlab_robochef import utils
from hcsvlab_robochef import metadata
from hcsvlab_robochef.ingest_base import IngestBase
from hcsvlab_robochef.utils.serialiser import Serialiser
from hcsvlab_robochef.annotations import *
from hcsvlab_robochef.utils.statistics import *
from hcsvlab_robochef.annotations.annotated_text import *
from hcsvlab_robochef.annotations.annotation import *

from xml.etree import ElementTree as et
from rdf import braidedMap

class BraidedIngest(IngestBase):
  
  filemetadata = {}
  META_DEFAULTS = {'language': 'eng'}


  def setMetaData(self, dirpath):
    ''' Braided obtains meta data during the ingest as there is not separate meta data file '''
    pass
 
 
  def ingestCorpus(self, srcdir, outdir):
 
    print "  converting corpus in", srcdir, "into normalised data in", outdir   
    print "    clearing and creating output location"
    
    self.clear_output_dir(outdir)
    
    # Obtain the list of source files we would like to process
    res = []
    utils.listFiles(res, srcdir, False)
    res = [x for x in res if os.path.splitext(x)[1] == ".xml"]
    
    sofar = 0
    total = len(res)
    print "    processing files..."
    
    #res = res[101:103] 
    
    for f in res:
    
      # TODO: get this guy working
      if os.path.basename(f) in ["c455d2f2-da9e-7bda-b18c-2e2ff045d208_1.xml"]:
        continue
    
      print sofar, "of", total, f, "\033[A"
      
      # SDP 28/02/2012: Changed ingestDocument to return the meta dictionary instead of the graph
      # as the graph is now generated by the generate_single_output function
      meta = self.ingestMetaData(f)
      transcript_files = self.__get_transcript(f, metadata, meta)
      raw, body, meta, anns, attachments = self.ingestDocument(f, meta)


      # Initialise the serialiser which produces all the output documents for this corpus
      ser = Serialiser(outdir)
      file_handler = FileHandler()
      original_doc = None
      compatriot_doc = None
      
      # First find the documents the meta data refers too
      for attachment in metadata.get_on_path(["item", "attachments", "attachment", "file"], meta):
        
        file_name = os.path.splitext(attachment)[0]
        file_extension = os.path.splitext(attachment)[1]
        
        # We can only process mp4 and pdf files at this stage
        if file_extension == '.mp4':
          
          compatriot_file = file_handler.findCompatriot(srcdir, file_name, r'^(.)+.mp4$', r'^[\w\d-]+.xml$')
          if compatriot_file is not None:
            compatriot_doc = { 'filetype': 'Video', 'sampleid': meta['sampleid'], 'sourcepath': compatriot_file}
            
        elif file_extension == '.pdf':
          original_doc = { 'filetype': 'Text', 'sampleid': meta['sampleid'], 'rawtext': raw, 'text': body, 'sourcepath': transcript_files[0]} 
          
      
      # Now use these documents to produced the serialised output
      if compatriot_doc is None and original_doc is None:
        ser.serialise_single(meta['sampleid'], 'braided', raw, body, braidedMap, meta, anns)
        
      else:
        if compatriot_doc is not None and original_doc is not None:
          ser.serialise_multiple(meta['sampleid'], (original_doc, compatriot_doc, ), 'braided', braidedMap, meta, anns)
          
        else:
          if original_doc is not None:
            ser.serialise_single(meta['sampleid'], 'braided', raw, body, braidedMap, meta, anns, transcript_files[0])
          else:
            ser.serialise_multiple(meta['sampleid'], (compatriot_doc, ), 'braided', braidedMap, meta, anns)
          
      sofar += 1
      
    print "\033[2K   ", total, "files processed"
  
  
  def ingestMetaData(self, filename):
    ''' Ingests the meta data from the source XML document '''
    xml_tree = et.parse(filename)
    d =  metadata.xml2dict(xml_tree.getroot(), ignore_root = True)
    d.update(self.META_DEFAULTS)
    d[u'sampleid'] = d["BC_identifier"]
    return d
    
    
  def ingestDocument(self, f, meta):
    
    transcript_files = self.__get_transcript(f, metadata, meta)
    all_attachments = metadata.get_on_path(["item", "attachments", "attachment", "file"], meta)
    
    text = ""
    body = ""
    if (len(transcript_files) > 0):
      text = subprocess.check_output(["pdftotext", "-enc", "UTF-8", "-nopgbrk", "-layout", transcript_files[0], "-"]) # NOTE: Only taking the first pdf we find.
      text = text.decode('utf-8')
      fh = open("last_processed_file", "w")
      fh.write(text.encode('utf-8'))
      fh.close
      parsed = self.parseFile(text)
      body = parsed.pop("body")
      meta.update(parsed)
      at = self.parse_annotations(body)

      # the participants property will have some people in it
      if meta.has_key('infile_participants'):
          participants = meta['infile_participants'][0]
          for id in participants.keys():
              info = dict()
              if participants[id] in ['Interviewer', 'Respondent']:
                  info['role'] = participants[id]
              else:
                  info['name'] = participants[id]
                  
              info['id'] = meta['sampleid']+'#'+id
              meta['table_person_'+info['id']] = info 
       
      # we return one extra parameter because we need the set of attached files to include will be pulled from the meta data.
      return (text, at[0].text, meta, at[0].anns, all_attachments)
    else:
      return (text, "", meta, "", all_attachments)
  
  
  def speaker_token(self):
    return (Suppress(LineEnd()) + Word(u"ABCDEFGHIJKLMNOPQRSTUVWXYZ")+Suppress(OneOrMore(White(" ")))).leaveWhitespace()


  def parseFile(self, text):
    title = (SkipTo(LineEnd()).leaveWhitespace()+ FollowedBy(LineEnd())).setParseAction(lambda s, loc, toks: "".join(toks).strip())
    date = Optional(Suppress(LineEnd()) + Word(nums) + Word(alphas) + Word(nums) + FollowedBy(LineEnd())).setParseAction(lambda s, loc, toks: " ".join(toks))
    note = (Suppress(LineEnd()) + CharsNotIn("=\n").setParseAction(lambda s, loc, toks: [s.strip() for s in toks]) + FollowedBy(LineEnd())).leaveWhitespace()
    def extractParticipants(s, loc, toks):
      participants = {}
      for i in range(0, len(toks), 2):
       participants[toks[i]] = toks[i+1].strip()
      return participants
    parti_title = Word(alphas.upper()) + Suppress("=")
    participants = (Suppress(LineEnd()) + Suppress(ZeroOrMore(White(" "))) + OneOrMore(parti_title + SkipTo(parti_title ^ White("\n")))).setParseAction(extractParticipants)
    meta_parser = title.setResultsName("infile_title")   \
                + date.setResultsName("infile_date")     \
                + OneOrMore(note).setParseAction(lambda s, loc, toks: " ".join(toks)).setResultsName("infile_notes") \
                + Optional(participants).setResultsName("infile_participants") \
                + Optional(SkipTo(self.speaker_token())).setResultsName("infile_notes2") \
                + Suppress(Optional(White(" \t\n"))) \
		+ CharsNotIn(u"").setResultsName("body")
    
    return meta_parser.parseString(text)


  def parse_annotations(self, text):
    speaker = (self.speaker_token() \
	    + SkipTo((self.speaker_token() ^ StringEnd()), False)).setParseAction(lambda s, loc, toks: AnnotatedText(toks[1],[Annotation("speaker", toks[0], 0, len(toks[1]))]))
   # speakers = (SkipTo(speaker_token).leaveWhitespace().setParseAction(lambda s, loc, toks: AnnotatedText(toks[0], [])) \
    speakers = OneOrMore(speaker).setParseAction(lambda s, loc, toks: concat(toks, sep="\n", extend = False))
    
    return speakers.parseString("\n" + text)  # note we need to add back in the newline we lost
    
    
  def __get_transcript(self, f, metadata, meta):
    ''' Return a list of transcript files for the corresponding input xml document '''
    return map(lambda fn: os.path.join(os.path.splitext(f)[0], fn), filter(lambda fn: os.path.splitext(fn)[1] == ".pdf", metadata.get_on_path(["item", "attachments", "attachment", "file"], meta)))
