import sys
import os
import json
import fnmatch
import re
from rdflib import Graph
import rdfextras

COLLECTION_QUERY = """SELECT DISTINCT ?coll
                   WHERE {
                    ?item <http://purl.org/dc/terms/isPartOf> ?coll .
                }"""

ITEM_QUERY = """SELECT DISTINCT ?item ?identifier
                   WHERE {
                    ?item a <http://ns.ausnc.org.au/schemas/ausnc_md_model/AusNCObject> .
                    ?item <http://purl.org/dc/terms/identifier> ?identifier .
                    ?item <http://purl.org/dc/terms/isPartOf> ?corpus .
                }"""

DOCUMENT_QUERY = """SELECT DISTINCT ?type ?identifier ?source
                   WHERE {
                    ?doc <http://purl.org/dc/terms/type> ?type .
                    ?doc <http://purl.org/dc/terms/identifier> ?identifier .
                    ?doc <http://purl.org/dc/terms/source> ?source .
                }"""


def create_manifest(srcdir, format):
    rdf_files = get_files(srcdir)

    sofar = 0
    manifest_hash = {}

    for rdf in rdf_files:
        if sofar == 0:
            manifest_hash = {"collection_name":extract_manifest_collection(rdf, format), "files":{}}

        filename = os.path.basename(rdf)

        graph = Graph()
        graph.parse(rdf, format=format)

        res = graph.query(ITEM_QUERY)
        if len(res) == 0:
            print "No Item info found in rdf file ", filename
            exit()
        else:
            for row in res:
                entry = {"id":str(row[1]), "uri":str(row[0]), "docs":[]}
                break

        res = graph.query(DOCUMENT_QUERY)
        for row in res:
            entry["docs"].append({"identifier":str(row[1]), "source":str(row[2]), "type":str(row[0])})

        manifest_hash["files"][filename] = entry

        sofar = sofar + 1
        print "\033[2K   ", sofar, os.path.basename(rdf), "\033[A"

    with open(os.path.join(srcdir, "manifest.json"), 'w') as outfile:
        json.dump(manifest_hash, outfile, indent=True)

    print "\033[2K   ", sofar, "files processed"

def get_files(srcdir):

    item_pattern = ".*-metadata.rdf"

    for root, dirnames, filenames in os.walk(srcdir):
        for filename in filenames:
            if re.match(item_pattern, filename):
                yield os.path.join(root, filename)

def extract_manifest_collection(rdf_file, format):
    graph = Graph()
    graph.parse(rdf_file, format=format)
    
    res = graph.query(COLLECTION_QUERY)
    # Small hack for austalk
    for row in res:
        if str(row[0]) == "http://ns.austalk.edu.au/corpus":
            return "austalk"
    for row in res:
        return os.path.basename(row[0])
    return ""