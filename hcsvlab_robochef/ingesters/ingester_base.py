import os
import shutil

from abc import ABCMeta, abstractmethod
from hcsvlab_robochef import configmanager
from hcsvlab_robochef.utils.manifester import *


class IngesterBase(object):

    __metaclass__ = ABCMeta
    '''
    This abstract class is a representation of an ingester. It is being used in-lieu of an interface
    '''

    configmanager.configinit()


    @abstractmethod
    def create_n3():
        ''' Ingest collection level metadata '''
        return None


    @abstractmethod
    def set_metadata():
        ''' Loads the meta data for use during ingest '''
        return None
      
    
    @abstractmethod
    def ingest_corpus():
        '''
        The ingest entry point where an input and output directory is specified 
        '''
        return None
      
      
    @abstractmethod
    def ingest_document():
        '''
        Ingest a specific source document, from which meta-data annotations and raw data is produced
        '''
        return None


    @abstractmethod
    def identify_documents():
        '''
        Identifies the indexable and display documents from the given documents according to the collection rule
        '''
        return (None, None)


    def clear_output_dir(self, outdir):
        ''' Clears the output directory '''
        if os.path.exists(outdir):
            shutil.rmtree(outdir)
        os.mkdir(outdir)


    def generate_manifest(self):
        ''' Creating the manifest file and putting in output directory '''
        print "    creating collection manifest file for " + self.output_dir
        create_manifest(self.output_dir, self.manifest_format)


