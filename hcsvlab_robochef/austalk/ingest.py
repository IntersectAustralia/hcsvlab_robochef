import os
import re
import glob
import urlparse

from hcsvlab_robochef.ingest_base import IngestBase
from hcsvlab_robochef.rdf.namespaces import *
from rdflib import Graph, Namespace, Literal
import rdfextras
from hcsvlab_robochef import configmanager

configmanager.configinit()

FILES_FILE_SUFFIX = "-files"
DOWNSAMPLED_FILE_SUFFIX = "-ds"
METADATA_FILE_SUFFIX = "-metadata"
UNSOURCED_QUERY = """SELECT DISTINCT ?item ?doc
                   WHERE {
                    ?item <http://ns.ausnc.org.au/schemas/ausnc_md_model/document> ?doc .

                }"""

DOCUMENT_QUERY = """SELECT DISTINCT ?doc ?source
                   WHERE {
                    ?doc <http://purl.org/dc/terms/type> ?type .
                    ?doc <http://purl.org/dc/terms/identifier> ?identifier .
                    ?doc <http://purl.org/dc/terms/source> ?source .
                }"""

DISPLAY_DOC_QUERY = """SELECT ?item ?doc WHERE {
        ?item <http://ns.ausnc.org.au/schemas/ausnc_md_model/document> ?doc .
        ?doc <http://ns.austalk.edu.au/channel> "ch6-speaker16" .
        }"""

RDF_FORMAT = "nt"
RDF_OUTPUT_FORMAT = "turtle"


class AustalkIngest(IngestBase):
    def setMetaData(self, srcdir):
        pass

    def ingestCorpus(self, srcdir, outdir):
        ''' This function will initiate the ingest process for the Austalk corpus '''
        ''' It assumes a set of pre-processed .nt files which we need to concatenate and add document sources '''
        ''' Assumes files are stored in site directories (e.g. ANU, USYD etc) inside a parent "metadata" directory '''

        print "  converting corpus in", srcdir, "into normalised data in", outdir
        print "    clearing and creating output location"

        self.clear_output_dir(outdir)

        print "    processing files..."

        files_to_process = self.__get_files(srcdir)
        sofar = 0

        for files_metadata in files_to_process:
            item_metadata = files_metadata.replace(FILES_FILE_SUFFIX, "")
            downsampled_doc = files_metadata.replace(FILES_FILE_SUFFIX, DOWNSAMPLED_FILE_SUFFIX)

            if not os.path.exists(item_metadata) or not os.path.exists(downsampled_doc):
                print "Missing files - " + item_metadata
                continue

            split_path = item_metadata.split("/")
            subdir = split_path[split_path.index("metadata") + 1]
            if not os.path.exists(os.path.join(outdir, subdir)):
                os.mkdir(os.path.join(outdir, subdir))

            outfile = os.path.join(outdir, subdir, os.path.basename(item_metadata)).replace("."+RDF_FORMAT, "%s.rdf" % METADATA_FILE_SUFFIX)

            # concatenate all metadata files
            graph = read_metadata_files(item_metadata)

            # determine which document will be the display document
            identify_display_document(graph)

            # add document references to graph
            document_mapping = write_document_results_to_file(graph)

            # make data URIs point to our own server
            graph_text = map_data_uris(graph, document_mapping)

            # output the new graph
            with open(outfile, "a") as rdf_file:
                print >> rdf_file, graph_text

            sofar = sofar + 1
            print "\033[2K   ", sofar, os.path.basename(item_metadata), "\033[A"

        print "\033[2K   ", sofar, "files processed"

    def ingestDocument(self, srcdir, sourcepath):
        pass

    def __get_files(self, srcdir):
        ''' This function generates a sequence of files that
        the Austalk ingest should actually process
        Note this is a generator (using yield)'''

        item_pattern = "[1-4]_[0-9]+_[123]_[0-9]+_[0-9]+-files\.nt"

        for root, dirnames, filenames in os.walk(srcdir):
            for filename in filenames:
                if re.match(item_pattern, filename):
                    yield os.path.join(root, filename)


def read_metadata_files(item_metadata):
    """Read all metadata files matching the item basename into a single
    graph, return the graph"""

    g = Graph()
    (basename, ext) = os.path.splitext(item_metadata)
    for filename in glob.glob(basename + "*"):
        g.parse(filename, format=RDF_FORMAT)

    return g


def write_document_results_to_file(graph):
    mappings = {}
    results = graph.query(UNSOURCED_QUERY)
    for row in results:
        (item, document) = row

        obj = document.replace("http://data.austalk.edu.au/", configmanager.get_config("DOCUMENT_BASE_URL") + configmanager.get_config("AUSTALK") + "/")
        subject = item.replace("http://id.austalk.edu.au/item", corpus_prefix_namespace(configmanager.get_config("AUSTALK"))) + "/document/" + os.path.basename(obj)

        mappings[item] = item.replace("http://id.austalk.edu.au/item", corpus_prefix_namespace(configmanager.get_config("AUSTALK")))
        mappings[document] = subject

        graph.add((Namespace(subject), DC.source, Literal(obj)))
        graph.add((Namespace(subject), DC.extent, Literal(os.path.getsize(urlparse.urlparse(obj).path))))

    results = graph.query(DOCUMENT_QUERY)
    for row in results:
        (document, source) = row
        obj = source.replace("http://data.austalk.edu.au/", configmanager.get_config("DOCUMENT_BASE_URL") + configmanager.get_config("AUSTALK") + "/")
        subject = document
        graph.set((Namespace(subject), DC.source, Literal(obj)))
        graph.add((Namespace(subject), DC.extent, Literal(os.path.getsize(urlparse.urlparse(obj).path))))

    return mappings

def identify_display_document(graph):
    """Find the ch6-speaker16 document for this item and mark it as the
    display document by adding a triple to the graph"""

    results = graph.query(DISPLAY_DOC_QUERY)
    for row in results:

        (item, document) = row
        graph.add((item, ALVEO.display_document, document))



def map_data_uris(graph, document_mapping):
    """Modify the RDF to change the URI of all data items to our own
    configured server.  Return a serialisation of the graph."""
    bind_graph(graph)
    document = graph.serialize(format=RDF_OUTPUT_FORMAT)
    for k in document_mapping.keys():
        document = document.replace(k, document_mapping[k])

    return document


# note that this could also map item urls, currently http://id.austalk.edu.au/item/



