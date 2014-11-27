import os
import hcsvlab_robochef
# import string

from abc import ABCMeta, abstractmethod
from rdflib import plugin
from rdflib.serializer import Serializer


class GraphSerialiser(object):
    __metaclass__ = ABCMeta
    '''
    This class is essentially an asbtract base class. All serialisers for RDF inherit from this base class
    '''

    @abstractmethod
    def serialise(self, outdir, sampleid, meta_map, ann_dict):
        '''
        All serialisers implement this method which produces the relevant serial form
        '''
        return None


class MetaSerialiser(GraphSerialiser):
    # TODO: can replace the tuplelist param with a check if meta_dict is of type dict or list
    def serialise(self, outdir, sampleid, meta_map, meta_dict, document_identifier, tuplelist=False):
        '''
        This function converts a dictionary of meta values to a graph representing such values.
        This graph is then serialised to disk.
        '''
        if meta_dict is not None and len(meta_dict) > 0:

            if tuplelist:
                metadata_graph = meta_map.map_tuplelist(meta_dict, document_identifier)
            else:
                metadata_graph = meta_map.mapdict(meta_dict, document_identifier)

            if metadata_graph is not None:
                serializer = plugin.get('turtle', Serializer)(metadata_graph)
                f = open(os.path.abspath(os.path.join(outdir, sampleid + "-metadata.rdf")), 'w')
                serializer.serialize(f, encoding='utf-8')
                f.close()

            # Return whatever mapdict function call produces
            return metadata_graph


class AnnotationSerialiser(GraphSerialiser):
    def serialise(self, outdir, sampleid, meta_map, ann_dict):
        '''
        This function converts a dictionary of annotations to a graph representing such annotations.
        This graph is then serialised to disk.
        '''
        if ann_dict is not None and len(ann_dict) > 0:
            acol = hcsvlab_robochef.annotations.AnnotationCollection(ann_dict, sampleid, meta_map)
            ann_graph = acol.to_rdf()

            # write out annotations
            if ann_graph is not None:
                serializer = plugin.get('turtle', Serializer)(ann_graph)
                f = open(os.path.abspath(os.path.join(outdir, sampleid + "-ann.rdf")), 'w')
                serializer.serialize(f, encoding='utf-8')
                f.close()

            # Note how we return the graph even if it might be None
            return ann_graph