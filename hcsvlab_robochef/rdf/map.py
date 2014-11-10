"""Mapping property names and values for metadata and annotation ingest"""


from rdflib import Namespace, Graph, Literal
from rdflib.term import URIRef
from hcsvlab_robochef.utils.parsing import toXMLName
from namespaces import *

import time
import urllib

from hcsvlab_robochef import configmanager
configmanager.configinit()

def get_generic_doc_mapper():
    ''' This function returns a generic mapping for FOAF documents '''

    docMapper = FieldMapper(AUSNC)

    # docMapper.add('filesize', mapto=AUSNC.documentsize) # ? DC.extent
    docMapper.add('filesize', mapto=DC.extent)

    # docMapper.add('filetype', mapto=AUSNC.documenttype) # ? DC.format or DC.type. Format seems better
    docMapper.add('filetype', mapto=DC.type)

    # docMapper.add('filelocation', mapto=AUSNC.documentlocation) # ? DC.source
    docMapper.add('filelocation', mapto=DC.source)

    # docMapper.add('filename', mapto=AUSNC.documentname) # ? DC.identifier
    docMapper.add('filename', mapto=DC.identifier)

    docMapper.add('documenttitle', mapto=DC.title)

    return docMapper

def metadata_defaults(metadataMapper):
  metadataMapper.add('language', mapto=OLAC.language)


def dictmapper(dictionary):
    """Return a function to map property values
    via a dictionary lookup in the given dictionary"""

    def fn(prop, val):
        if dictionary.has_key(val):
            return ((prop, dictionary[val]),)
        else:
            return ((prop, Literal(val)),)

    return fn



class FieldMapper:
    """Class representing a mapping of field names and values"""

    # class variables to collect class and predicates used
    classes = []
    predicates = []

    def __init__(self, corpusID):
        """Create a Field Mapper

        corpusID is an indentifier for the corpus which will be used
        in the default schema and corpus item namespaces (eg. ACE)
        """

        self.corpusID = corpusID

        self.simpleMap = dict() # a dict of simple key to key mappings
        self.graph = Graph(identifier=self.corpus_uri())

    def __call__(self, key, value):
        """Callable interface to map a single property/value pair"""

        return self.map(key, value)


    def add(self, key, mapto=None, ignore=False, mapper=None):
        """Add a mapping to the mapper.
        key is the key that triggers this mapping
        mapto is a simple RDF property, if present this will be the output property
        ignore - if True, this property will be ignored, no output
        mapper - another mapper object that will be used to map properties
           in the value of this property - ie. for when the value is a nested
           property list (like speaker info)  OR mapper is a function(property, value) that
           returns a (property, RDFValue) pair where property is a valid RDF property and
           RDFvalue is either a Literal or Resource value.
        transform - a function that transforms the (key, value) pair"""


        # clean up the property name before we store it
        key = toXMLName(unicode(key))

        if ignore:
            self.simpleMap[key] = 'IGNORE'
        elif mapto and mapper:
            self.simpleMap[key] = (mapto, mapper)
        elif mapto:
            self.simpleMap[key] = mapto
        elif mapper:
            self.simpleMap[key] = mapper

    def map(self, key, value):
        """Return a sequence of pairs (property, mappedvalue) which is the mapping
        for the given key/value pair in the mapping
        Returns ((None, None),) in the case when no mapping can be made"""

        # ignore terms with empty values
        if type(value) == unicode and value.strip() == "":
            return ((None, None),)

        # clean up the property name before we start converting
        key = toXMLName(unicode(key))

        if self.simpleMap.has_key(key):
            if self.simpleMap[key] == 'IGNORE':
                return ((None, None),)
            elif type(self.simpleMap[key]) == tuple:
                (prop, mapper) = self.simpleMap[key]
                # we delegate to the mapper
                return mapper(prop, value)
            elif type(self.simpleMap[key]) == URIRef:
                # value is unchanged
                return ((self.simpleMap[key], Literal(value)),)

        #print "No map entry for ", key

        # if we don't know it, remove table_ from the front and
        # place the property in the default namespace
        # and record it with a literal value
        if key.startswith("table_"):
            prop = key[6:]
        elif key.startswith('item_'):
            prop = key # key[5:]
        else:
            prop = key
        # default properties go in the AUSNC namespace
        # and make sure it will generate a valid XMLName.
        prop = AUSNC[prop]

        if self.simpleMap.has_key(key):
            # one remaining option is that the value is a mapping
            # function, so we call that and return the result
            return self.simpleMap[key](prop, value)
        else:
            # just use this property and the unchanged value
            return ((prop, Literal(value)),)


    def corpus_uri(self):
        """Generate a URI for the corpus that this item is part of"""

        return corpus_uri(self.corpusID)

    def item_uri(self, id):
        """Generate a URI for this item"""
        return corpus_item_uri(self.corpusID, id)


    def speaker_uri(self, id):
        """Generate a speaker URI for this corpus"""

        return corpus_speaker_uri(self.corpusID, id)

    def item_source_uri(self, id):
        """Generate a URI for the source data of this item"""

        return corpus_source_uri(self.corpusID, id)


    def mapdict(self, metadata):
        '''
        This function takes one metadata dictionary as extracted by the ingest
        module in this package, and returns a rdflib Graph instance.
        '''

        graph = Graph(identifier=self.corpus_uri())
        graph = bind_graph(graph)

        itemuri = self.item_uri(metadata['sampleid'])

        for key in metadata.keys():
            if type(metadata[key]) == str and metadata[key].strip() != "":
                # convert and add the property/value
                for (prop, value) in self.map(key, metadata[key]):
                    if prop:
                        graph.add((itemuri, prop, value))

        self.update_schema(graph)
        return graph


    def update_schema(self, graph):
        """Generate a list of classes and properties used in this graph
        which might form the basis of a schema, store them in
        class variables
        """

        classes = graph.objects(predicate=RDF.type)
        predicates = graph.predicates()

        for c in classes:
            if not c in self.classes:
                self.classes.append(c)

        for p in predicates:
            if not p in self.predicates:
                self.predicates.append(p)


    @classmethod
    def generate_schema(cls):
        """Using the recorded classes and predicates lists,
        generate a proto-schema"""

        schema = Graph()
        schema.bind('owl', OWL)
        schema.bind('rdf', RDF)
        schema.bind('rdfs', RDFS)
        schema.bind('foaf', FOAF)

        for c in cls.classes:
            schema.add((c, RDF.type, OWL.Class))
            schema.add((c, RDFS.label, Literal("LABEL")))

        for p in cls.predicates:
            schema.add((p, RDF.type, OWL.DataTypeProperty))
            schema.add((p, RDFS.label, Literal("PREDICATE")))
            schema.add((p, OWL.domain, AUSNC.AusNCObject))
            schema.add((p, OWL.range, XSD.String))

        return schema


class MetadataMapper(FieldMapper):
    """Mapper class for metadata that might include nested speaker descriptions"""


    def __init__(self, corpusID, speakerMap=None, documentMap=None):
        """Create a Metadata Mapper

        corpusID is an indentifier for the corpus which will be used
        in the default schema and corpus item namespaces (eg. ACE)

        speakerMap is an optional Metadata Mapper used to map fields
        for any table_person included in the data

        documentMap is an optional Metadata Mapper used to map fields
        for any table_document included in the data
        """

        FieldMapper.__init__(self, corpusID)

        self.speakerMap = speakerMap
        self.documentMap = documentMap


    def mapdict(self, metadata, identify_documents):
        '''
        This function takes one metadata dictionary as extracted by the ingest
        module in this package, and returns a rdflib Graph instance.
        '''

        graph = Graph(identifier=self.corpus_uri())
        graph = bind_graph(graph)

        itemuri = self.item_uri(metadata['sampleid'])
        sourceuri = self.item_source_uri(metadata['sampleid'])
        corpusuri = self.corpus_uri()
        documents = []

        for key in metadata.keys():
            if key == 'sampleid':
                pass
            elif type(metadata[key]) == str and metadata[key].strip() == "":
                # don't record empty fields
                pass
            elif key.startswith("table_person"):
                speakermeta = metadata[key]
                # make a speaker uri
                speakeruri = self.speaker(speakermeta, graph)
                graph.add((itemuri, OLAC.speaker, speakeruri))

            elif key.startswith("table_document"):
                docmeta = metadata[key]
                # make a document uri
                docuri = self.document(docmeta, graph)
                docmeta.update({'uri':docuri})
                documents.append(docmeta)
                graph.add((itemuri, AUSNC.document, docuri))  # TODO: what is a document?
                # add a property recording a URI for the document if
                # we're given a  DOCUMENT_BASE_URL in the configuration

                baseuri = configmanager.get_config("DOCUMENT_BASE_URL", "")
                if not baseuri == "":
                    docid = docmeta['filename']
                    docid = urllib.quote(docid)
                    if 'subdir' in metadata:
                      uri = URIRef(baseuri + self.corpusID.lower() + metadata['subdir'] + docid)
                    else:
                      if self.corpusID.lower() == "paradisec":
                        uri = URIRef(baseuri + self.corpusID.lower() + "/" + docid.split("-")[0] + "/" + docid.split("-")[1] + "/" + docid)
                      else:
                        uri = URIRef(baseuri + self.corpusID.lower() + "/" + docid)
                    graph.add((docuri, DC.source, URIRef(uri)))


            elif  metadata[key] != '':
                # convert and add the property/value
                try:
                  for (prop, value) in self.map(key, metadata[key]):
                      if prop:
                          #print itemuri, prop, value
                          graph.add((itemuri, prop, value))
                except ValueError:
#                  print key
                  pass

        # type infos:
        graph.add((itemuri, RDF.type, AUSNC.AusNCObject))

        # we want to say that this item is part of it's corpus
        graph.add((itemuri, DC.isPartOf, corpusuri))

        (indexable_document, display_document) = identify_documents(documents)

        # 13/03/2012 SDP: The use of dc:source is not supported as we are using document instead
        if indexable_document:
          graph.add((itemuri, ALVEO.indexable_document, indexable_document))

        if display_document:
          graph.add((itemuri, ALVEO.display_document, display_document))

        # graph.add((sourceuri, RDF.type, FOAF.Document))
        # link item to other objects:
        # graph.add((itemuri, DC.source, sourceuri))
        # g.add((itemuri, DC.creator, authoruri))
        # keep original item identifier as separate field

        # TODO: should we derive a new property from dc:identifier?
        graph.add((itemuri, DC.identifier, Literal(metadata['sampleid'])))

        self.update_schema(graph)

        return graph

    def map_tuplelist(self, metadata, identify_documents):
        graph = Graph(identifier=self.corpus_uri())
        graph = bind_graph(graph)
        documents = []

        itemuris = [v for k,v in metadata if 'URI' in k]

        if itemuris:
          itemuri = Namespace(itemuris[0])
          for k, v in metadata:
              if k.startswith("table_document"):
                docmeta = v
                docuri = self.document(docmeta, graph)
                docmeta.update({'uri':docuri})
                documents.append(docmeta)
                graph.add((itemuri, AUSNC.document, docuri))
                baseuri = configmanager.get_config("DOCUMENT_BASE_URL", "")
                if not baseuri == "":
                    docid = docmeta['filename']
                    docid = urllib.quote(docid)
                    if 'subdir' in metadata:
                      uri = URIRef(baseuri + self.corpusID.lower() + metadata['subdir'] + docid)
                    elif self.corpusID.lower() == "paradisec":
                      subdir = docid.split("-")[0] + "/" + docid.split("-")[1] + "/"
                      uri = URIRef(baseuri + self.corpusID.lower() + "/" + subdir + docid)
                    else:
                      uri = URIRef(baseuri + self.corpusID.lower() + "/" + docid)
                    graph.add((docuri, DC.source, URIRef(uri)))
              elif k.startswith("table_person"):
                speakermeta = v
                speakeruri = self.speaker(speakermeta, graph)
                graph.add((itemuri, speakermeta['role'], speakeruri))
              else:
                for (prop, value) in self.map(k, v):
                    if prop:
                        graph.add((itemuri, prop, value))

          corpusuri = self.corpus_uri()
          graph.add((itemuri, RDF.type, AUSNC.AusNCObject))
          graph.add((itemuri, DC.isPartOf, corpusuri))

          (indexable_document, display_document) = identify_documents(documents)

          if indexable_document:
              graph.add((itemuri, ALVEO.indexable_document, indexable_document))

          if display_document:
              graph.add((itemuri, ALVEO.display_document, display_document))

          self.update_schema(graph)
        else:
          graph = None
        return graph


    def speaker(self, metadata, graph):
        """Generate the description of a speaker from a metadata dictionary
        adds triples to the item's graph, returns the speaker URI"""

        if not self.speakerMap:
            raise Exception("Can't map speaker - no speaker map provided")

        if not metadata.has_key("id"):
            raise Exception("No id for speaker")

        speakeruri = self.speaker_uri(metadata["id"])

        graph.add((speakeruri, RDF.type, FOAF.Person))

        for key in metadata.keys():
            if key is "id":
                pass
            else:
                for (prop, value) in self.speakerMap(key, metadata[key]):
                    if prop and value:
                        graph.add((speakeruri, prop, value))

        return speakeruri



    def document(self, metadata, graph):
        """Generate the description of a document from a metadata dictionary
        adds triples to the item's graph, returns the document URI"""

        if not self.documentMap:
            raise Exception("Can't map document - no document map provided")

        if not metadata.has_key("id"):
            raise Exception("No id for document")

        uri = self.item_source_uri(metadata["id"])

        graph.add((uri, RDF.type, FOAF.Document))

        for key in metadata.keys():
            if key is "id":
                pass
            else:
                for (prop, value) in self.documentMap(key, metadata[key]):
                    if prop:
                        graph.add((uri, prop, value))

        return uri
