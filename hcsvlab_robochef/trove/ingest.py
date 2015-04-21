from hcsvlab_robochef.annotations import *
from hcsvlab_robochef.ingest_base import IngestBase
from hcsvlab_robochef.rdf.map import *
from hcsvlab_robochef.utils.serialiser import *
from hcsvlab_robochef.utils.statistics import *
from rdf import troveMap
import json
import os

class TroveIngest(IngestBase):

  def setMetaData(self, srcdir):
    pass

  def ingestCorpus(self, srcdir, outdir):
    files = self.__get_files(srcdir)

    total = len(files.keys())
    count = 0
    for name, path in files.iteritems():
      print count, " of ", total, "\033[A"
      self.ingestDocument(name, path, outdir)    
      count += 1
    
    print "\033[2K   ", total, "files processed"

          
  def ingestDocument(self, name, sourcepath, outdir):
    f = open(sourcepath, 'r')

    data = json.load(f)
    data['sampleid'] = data['id']
    serialiser = Serialiser(outdir)
    serialiser.serialise_single(name, 'trove', data['fulltext'], data['fulltext'], troveMap, data, None, self.identify_documents)


  def __get_files(self, srcdir):
    filehandler = FileHandler()
    files = filehandler.getFiles(srcdir, r'^.+\.json$')
    return files
