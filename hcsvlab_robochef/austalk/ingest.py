import os
import fnmatch

from hcsvlab_robochef.ingest_base import IngestBase
from hcsvlab_robochef.rdf.namespaces import *
from rdflib import Graph, Namespace, Literal
import rdfextras
from hcsvlab_robochef import configmanager
configmanager.configinit()

FILES_FILE_SUFFIX = "-files"
DOWNSAMPLED_FILE_SUFFIX = "-ds"
METADATA_FILE_SUFFIX = "-metadata"
DOCUMENT_QUERY = """SELECT DISTINCT ?item ?doc
				   WHERE {
			   		?item <http://ns.ausnc.org.au/schemas/ausnc_md_model/document> ?doc .
		   		}"""

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
		total = len(files_to_process)
		sofar = 0

		for files_metadata in files_to_process:
			item_metadata = files_metadata.replace(FILES_FILE_SUFFIX, "")
			downsampled_doc = files_metadata.replace(FILES_FILE_SUFFIX, DOWNSAMPLED_FILE_SUFFIX)

			if not os.path.exists(item_metadata) or not os.path.exists(downsampled_doc):
				print "Missing files - " + item_metadata
				continue

			split_path = item_metadata.split("/")
			subdir = split_path[split_path.index("metadata")+1]
			if not os.path.exists(os.path.join(outdir, subdir)):
				os.mkdir(os.path.join(outdir, subdir))

			outfile = os.path.join(outdir, subdir, os.path.basename(item_metadata)).replace(".nt", "%s.rdf" % METADATA_FILE_SUFFIX)

			# concatenate all metadata files
			concatenate_metadata_files(outfile, item_metadata, downsampled_doc, files_metadata)

			# add in downsampled source
			add_downsampled_document_source(outfile, downsampled_doc)

			# add in sources for other documents
			add_other_document_sources(outfile, files_metadata)

			sofar = sofar + 1
			print "\033[2K   ", sofar, "of", total, os.path.basename(item_metadata), "\033[A"

		print "\033[2K   ", total, "files processed"

	def ingestDocument(self, srcdir, sourcepath):
		pass

	def __get_files(self, srcdir):
		''' This function retrieves a list of files that the Austalk ingest should actually process '''
		return_files = []

		for root, dirnames, filenames in os.walk(srcdir):
			for filename in fnmatch.filter(filenames, '*%s.nt' % FILES_FILE_SUFFIX):
				return_files.append(os.path.join(root, filename))

		return return_files

def concatenate_metadata_files(outfile, item_metadata, downsampled_doc, files_metadata):
	with open(outfile, "w+") as rdf_file:
		print >> rdf_file, open(item_metadata, "r").read()
		print >> rdf_file, open(downsampled_doc, "r").read()
		print >> rdf_file, open(files_metadata, "r").read()

def add_downsampled_document_source(outfile, downsampled_doc):
	ds_graph = Graph()
	ds_graph.parse(downsampled_doc, format="nt")

	res = ds_graph.query(DOCUMENT_QUERY)
	write_document_results_to_file(outfile, res, True)

def add_other_document_sources(outfile, files_metadata):
	files_graph = Graph()
	files_graph.parse(files_metadata, format="nt")

	res = files_graph.query(DOCUMENT_QUERY)
	write_document_results_to_file(outfile, res)

def write_document_results_to_file(outfile, results, display=False):
	g = Graph()
	for row in results:
		item = row[0]
		document = row[1]
		predicate = DC.source
		obj = document.replace("http://data.austalk.edu.au/", configmanager.get_config("DOCUMENT_BASE_URL") + configmanager.get_config("AUSTALK") + "/")
		g.add( (document, predicate, Literal(obj)) )
		if display:
			g.add( (item, ALVEO.display_document, document) )
	with open(outfile, "a") as rdf_file:
		print >> rdf_file, g.serialize(format="nt")
