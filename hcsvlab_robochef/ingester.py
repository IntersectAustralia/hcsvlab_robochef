import os
import shutil

from abc import ABCMeta, abstractmethod
from hcsvlab_robochef import configmanager
from hcsvlab_robochef.utils.manifester import *


class IngestBase(object):
    __metaclass__ = ABCMeta
    '''
    This abstract class is a representation of an ingest. It is being used in-lieu of an interface
    '''

    configmanager.configinit()


    @abstractmethod
    def setMetaData(srcdir):
        ''' Loads the meta data for use during ingest '''
        return None
      
    
    @abstractmethod
    def ingestCorpus(srcdir, outdir):
        '''
        The ingest entry point where an input and output directory is specified 
        '''
        return None
      
      
    @abstractmethod
    def ingestDocument(sourcepath):
        '''
        Ingest a specific source document, from which meta-data annotations and raw data is produced
        '''
        return None

    def identify_documents(self, documents):
        '''
        Identifies the indexable and display documents from the given documents according to the collection rule
        '''
        return (None, None)

    def clear_output_dir(self, outdir):
        ''' Clears the output directory '''
        if os.path.exists(outdir):
            shutil.rmtree(outdir)
        os.mkdir(outdir)

    def copy_collection_metadata(self, srcdir, outdir, filename, savename):
        ''' Copies the collection level metadata file to output directory '''
        print "    copying collection level metadata file..."
        metadata_file = os.path.join(srcdir, filename)
        if os.path.exists(metadata_file) and os.path.exists(outdir):
            shutil.copyfile(metadata_file, os.path.join(outdir,savename))

    def create_collection_manifest(self, srcdir, format):
        ''' Creating the manifest file and putting in output directory '''
        print "    creating collection manifest file for " + srcdir
        create_manifest(srcdir, format)