from hcsvlab_robochef.annotations import *
from hcsvlab_robochef.ingest_base import IngestBase
from hcsvlab_robochef.rdf.map import *
from hcsvlab_robochef.utils.filehandler import *
from hcsvlab_robochef.utils.serialiser import *
from hcsvlab_robochef.utils.statistics import *
from rdf import paradisecMap
from xml.etree import ElementTree as ET
import codecs
import mimetypes
import urllib
import re

class EopasTestIngest(IngestBase):

  olac_role_map = {'annotator' : OLAC.annotator, 'author' : OLAC.author, 'compiler' : OLAC.compiler,
                  'consultant' : OLAC.consultant, 'data_inputter' : OLAC.data_inputter,
                  'depositor' : OLAC.depositor, 'developer' : OLAC.developer, 'editor' : OLAC.editor,
                  'illustrator' : OLAC.illustrator, 'interpreter' : OLAC.interpreter,
                  'interviewer' : OLAC.interviewer, 'participant' : OLAC.participant,
                  'performer' : OLAC.performer, 'photographer' : OLAC.photographer,
                  'recorder' : OLAC.recorder, 'researcher' : OLAC.researcher,
                  'research_participant' : OLAC.research_participant, 'responder' : OLAC.responder,
                  'signer' : OLAC.signer, 'singer' : OLAC.singer, 'speaker' : OLAC.speaker,
                  'sponsor' : OLAC.sponsor, 'transcriber' : OLAC.transcriber, 'translator' : OLAC.translator }



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
      f = f.replace(srcdir, outdir, 1)
      try:
        os.makedirs(os.path.dirname(f))
      except:
        pass
      
      (sampleid, _) = os.path.splitext(f)

      serialiser = MetaSerialiser()
      serialiser.serialise(outdir, sampleid, paradisecMap, meta_dict, True)
    
    
      sofar = sofar + 1
      print "\033[2K   ", sofar, "of", total, f, "\033[A"
      
    print "\033[2K   ", total, "files processed"


  def setMetaData(self, rcdir):
    ''' Loads the meta data for use during ingest '''
    pass


  def ingestDocument(self, srcdir, sourcepath):
    """ Read and process a corpus document """
  
    xml_tree = self.__load_xml_tree(sourcepath)
    meta_dict = metadata.xml2paradisecdict(xml_tree, ['olac', 'metadata'])
    self.__get_documents(meta_dict)
    self.__get_people(meta_dict)
    return meta_dict


  def __get_documents(self, meta_dict):
    for k, v in meta_dict:
      if k == 'tableOfContents':
        filetype = self.__get_type(v) 
        file_meta = {'id' : v, 'filename' : v, 'filetype' : filetype, 'documenttitle' : v}
        meta_dict.append(('table_document_' + v, file_meta))
    meta_dict[:] = [(k, v) for k, v in meta_dict if 'tableOfContents' not in k]
        
        
  def __get_people(self, meta_dict):
    # TODO: maybe this belongs elsewhere
    roles = self.olac_role_map.keys()
    for k, v in meta_dict:
      if k in roles:
        person = {'role' : self.olac_role_map[k], 'id' : re.sub(' ', '_', v), 'name' : v}
        meta_dict.append(('table_person_' + k, person))
    meta_dict[:] = [(k, v) for k, v in meta_dict if k.strip() not in roles]
  
  
  # TODO: this could be moved to somewhere like ../utils where other modules could use it      
  def __get_type(self, filepath):
    url = urllib.pathname2url(filepath)
    mime_type, _ = mimetypes.guess_type(url)
    filetype = None
    if mime_type:
      filetype = mime_type.split('/')[0].title()
    if not filetype or filetype == 'Application':
      filetype = 'Other'
    return filetype


  def __get_files(self, srcdir):
    ''' This function retrieves a list of files that the HCSvLab ingest should actually process '''
    filehandler = FileHandler()
    
    files = filehandler.getFiles(srcdir, r'^.+?(?:pas|box).xml$')
    return_files = [os.path.join(srcdir, f) for f in files]
    return return_files    

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
    
    return ET.fromstring(text.encode("utf-8"))
